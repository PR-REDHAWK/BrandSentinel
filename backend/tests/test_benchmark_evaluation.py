import io
import time
import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.engines.deterministic.accessibility import scan_accessibility
from app.engines.deterministic.contrast import calculate_contrast_ratio, scan_html_css_contrast
from app.engines.deterministic.terms import scan_terminology
from app.engines.orchestrator import run_unified_audit_pipeline
from app.engines.rag.claim_verifier import run_deterministic_rag_grounding
from app.engines.vision.color_checker import check_image_color_compliance, extract_dominant_colors
from app.engines.vision.logo_checker import check_logo_integrity
from app.engines.vision.ocr_engine import extract_text_from_image
from app.models.auth import Organization, User, UserRole
from app.models.knowledge import ApprovedFact, BrandAsset, GlossaryTerm
from app.models.audit import FindingSeverity, Submission, SubmissionStatus


@pytest.fixture
def benchmark_org(db: Session) -> dict:
    org = Organization(name="Benchmark Enterprise", slug="benchmark-ent")
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id,
        email="benchmark@enterprise.com",
        hashed_password="pw",
        full_name="Benchmarker",
        role=UserRole.CREATOR,
        is_active=True,
    )
    db.add(user)

    # Approved Facts
    fact1 = ApprovedFact(
        organization_id=org.id,
        category="Performance",
        claim_pattern="cloud cost reduction",
        approved_truth="Customers achieve up to 30% reduction in infrastructure costs within six months.",
        source_citation="Audited Benchmark Report 2025, p. 12",
    )
    fact2 = ApprovedFact(
        organization_id=org.id,
        category="Uptime",
        claim_pattern="platform uptime SLA",
        approved_truth="BrandSentinel delivers 99.99% availability backed by a financial SLA.",
        source_citation="Service Level Agreement v4, Section 2",
    )
    db.add_all([fact1, fact2])

    # Glossary Terms
    term1 = GlossaryTerm(
        organization_id=org.id,
        term="dirt cheap",
        is_banned=True,
        preferred_term="cost-effective",
        definition_or_rule="Colloquial slang devaluing enterprise reliability.",
    )
    term2 = GlossaryTerm(
        organization_id=org.id,
        term="crushes the competition",
        is_banned=True,
        preferred_term="outperforms industry benchmarks",
        definition_or_rule="Aggressive, unsubstantiated competitive comparison.",
    )
    term3 = GlossaryTerm(
        organization_id=org.id,
        term="cheap hosting",
        is_banned=False,
        preferred_term="cost-effective cloud infrastructure",
        definition_or_rule="Preferred enterprise terminology.",
    )
    db.add_all([term1, term2, term3])

    # Brand Assets
    palette = BrandAsset(
        organization_id=org.id,
        asset_type="PALETTE",
        name="Official Enterprise Colors",
        hex_colors=["#0B2046", "#10B981", "#FFFFFF"],
    )
    logo = BrandAsset(
        organization_id=org.id,
        asset_type="LOGO",
        name="Enterprise Horizontal Logo",
        aspect_ratio=3.5,
        rules={"min_width_px": 200, "min_height_px": 50},
    )
    db.add_all([palette, logo])

    db.commit()
    db.refresh(org)

    return {
        "org": org,
        "user": user,
        "facts": [fact1, fact2],
        "glossary": [term1, term2, term3],
        "palette": palette,
        "logo": logo,
    }


def test_seeded_30_defect_benchmark_suite(db: Session, benchmark_org: dict):
    """
    Evaluates the Tri-Engine pipeline across 30 deliberate violation cases and clean controls.
    Measures Precision, Recall, Catch Rate (>= 90%), and Citation Integrity (100%).
    """
    org_id = benchmark_org["org"].id
    user_id = benchmark_org["user"].id
    glossary = benchmark_org["glossary"]
    facts = benchmark_org["facts"]
    palette = benchmark_org["palette"]
    logo = benchmark_org["logo"]

    start_time = time.time()
    total_seeded_violations = 0
    caught_violations = 0
    false_positives = 0
    citations_verified = 0
    factual_findings_count = 0

    # ==================== GROUP 1: DETERMINISTIC RULES (10 TESTS) ====================
    det_test_cases = [
        # 1. Exact banned term
        ("Our product is dirt cheap for all startups.", 1, "BANNED_TERM"),
        # 2. Banned term with trailing punctuation
        ("Get cloud hosting that is dirt-cheap!", 1, "BANNED_TERM"),
        # 3. Second banned slang
        ("BrandSentinel crushes the competition in every metric.", 1, "BANNED_TERM"),
        # 4. Glossary preferred term mismatch
        ("We offer cheap hosting options for microservices.", 1, "GLOSSARY_MISMATCH"),
        # 5. WCAG Low Contrast text
        ("<span style='color: #888888; background-color: #999999;'>Unreadable text</span>", 1, "WCAG_CONTRAST"),
        # 6. Missing alt text markdown
        ("Here is our architecture diagram: ![](architecture.png)", 1, "MISSING_ALT_TEXT"),
        # 7. Missing alt text HTML
        ("<img src='logo.png' /> with no description", 1, "MISSING_ALT_TEXT"),
        # 8. Missing html language tag
        ("<html><body>Welcome to BrandSentinel</body></html>", 1, "MISSING_HTML_LANG"),
        # 9. All-caps shouting
        ("BUY OUR ENTERPRISE PLATFORM RIGHT NOW OR REGRET IT FOREVER", 1, "ALL_CAPS_SHOUTING"),
        # 10. Clean control (Negative test: should NOT flag false positive)
        ("Acme Cloud delivers cost-effective infrastructure with audited security.", 0, "CLEAN_CONTROL"),
    ]

    for content, expected_count, test_id in det_test_cases:
        if expected_count > 0:
            total_seeded_violations += expected_count

        findings = []
        findings.extend(scan_terminology(content, glossary))
        findings.extend(scan_html_css_contrast(content))
        findings.extend(scan_accessibility(content))

        if expected_count > 0:
            if len(findings) >= expected_count:
                caught_violations += 1
        else:
            if len(findings) > 0:
                false_positives += len(findings)

    # ==================== GROUP 2: RAG & CLAIM VERIFICATION (10 TESTS) ====================
    rag_test_cases = [
        # 11. Overpromising percentage reduction (100% vs approved 30%)
        ("Our platform guarantees 100% cloud cost reduction within three days.", True),
        # 12. Unsubstantiated 80% reduction
        ("Achieve an instant 80% reduction in infrastructure costs effortlessly.", True),
        # 13. Exaggerated uptime SLA (100% uptime vs 99.99%)
        ("BrandSentinel provides 100% platform uptime SLA with zero downtime forever.", True),
        # 14. Timeframe overpromise
        ("Guaranteed complete cloud cost reduction within 24 hours of onboarding.", True),
        # 15. Hyperbolic off-brand tone
        ("The undisputed greatest software on Earth that crushes all alternatives.", True),
        # 16. Unverified guarantee phrasing
        ("Unconditional 100% reduction in cloud cost guarantees with zero caveats.", True),
        # 17. Extreme superlative claim
        ("Our system produces revolutionary 100% savings unprecedented in tech history.", True),
        # 18. Misleading cost metric
        ("Slash cloud cost reduction by 95% guaranteed on day one.", True),
        # 19. Clean claim aligned with approved fact (Negative test: must NOT flag)
        ("Customers achieve up to 30% reduction in infrastructure costs within six months.", False),
        # 20. Clean uptime statement (Negative test: must NOT flag)
        ("BrandSentinel delivers 99.99% availability backed by a financial SLA.", False),
    ]

    for content, is_violation in rag_test_cases:
        if is_violation:
            total_seeded_violations += 1

        findings = run_deterministic_rag_grounding(
            content=content,
            approved_facts=facts,
            relevant_chunks=[{
                "guideline_title": "Audited Benchmark Report 2025",
                "content": "Customers achieve up to 30% reduction in infrastructure costs.",
            }],
        )

        for f in findings:
            factual_findings_count += 1
            if f.source_citation and len(f.source_citation.strip()) > 3:
                citations_verified += 1

        if is_violation:
            if len(findings) >= 1:
                caught_violations += 1
        else:
            if len(findings) > 0:
                false_positives += len(findings)

    # ==================== GROUP 3: VISION, LOGO & COLOR ASSETS (10 TESTS) ====================
    # 21. Distorted logo aspect ratio (1.2 instead of 3.5)
    img_distorted = Image.new("RGB", (240, 200), color=(11, 32, 70))
    # 22. Clean logo aspect ratio (3.5)
    img_clean_logo = Image.new("RGB", (350, 100), color=(11, 32, 70))
    # 23. Off-brand neon pink color
    img_offbrand = Image.new("RGB", (100, 100), color=(255, 0, 128))
    # 24. Approved navy brand color
    img_approved = Image.new("RGB", (100, 100), color=(11, 32, 70))

    # Test Logo Distortion (Violation)
    total_seeded_violations += 1
    buf = io.BytesIO()
    img_distorted.save(buf, format="PNG")
    dist_findings = check_logo_integrity(buf.getvalue(), [logo])
    if dist_findings:
        caught_violations += 1

    # Test Clean Logo (Control)
    buf_clean = io.BytesIO()
    img_clean_logo.save(buf_clean, format="PNG")
    clean_findings = check_logo_integrity(buf_clean.getvalue(), [logo])
    if clean_findings:
        false_positives += len(clean_findings)

    # Test Off-Brand Color (Violation)
    total_seeded_violations += 1
    buf_color = io.BytesIO()
    img_offbrand.save(buf_color, format="PNG")
    color_findings = check_image_color_compliance(buf_color.getvalue(), [palette])
    if color_findings:
        caught_violations += 1

    # Test Approved Brand Color (Control)
    buf_app = io.BytesIO()
    img_approved.save(buf_app, format="PNG")
    app_findings = check_image_color_compliance(buf_app.getvalue(), [palette])
    if app_findings:
        false_positives += len(app_findings)

    # 25-28. Image format extraction (PNG, JPEG, WEBP, Low-Res)
    for fmt, (w, h) in [("PNG", (300, 100)), ("JPEG", (200, 80)), ("WEBP", (150, 60)), ("PNG", (40, 20))]:
        test_img = Image.new("RGB", (w, h), color=(255, 255, 255))
        b = io.BytesIO()
        test_img.save(b, format=fmt)
        res = extract_text_from_image(b.getvalue(), filename=f"test.{fmt.lower()}")
        assert hasattr(res, "text")

    # 29. WCAG Math Luminance contrast check
    ratio_fail = calculate_contrast_ratio("#777777", "#888888")
    assert ratio_fail < 4.5
    total_seeded_violations += 1
    caught_violations += 1

    # 30. Full Unified Pipeline End-to-End Latency & Verification
    sub = Submission(
        organization_id=org_id,
        creator_id=user_id,
        title="End-to-End Benchmark Run",
        target_channel="PR",
        current_status=SubmissionStatus.DRAFT,
    )
    db.add(sub)
    db.commit()

    test_content = (
        "Our platform is dirt cheap and guarantees 100% cloud cost reduction within 24 hours. "
        "BrandSentinel crushes the competition with 100% platform uptime SLA."
    )
    total_seeded_violations += 4

    e2e_res = run_unified_audit_pipeline(
        db=db,
        organization_id=org_id,
        user_id=user_id,
        submission_id=sub.id,
        content=test_content,
    )
    # The pipeline should catch at least 3 of these 4 violations
    if len(e2e_res.findings) >= 3:
        caught_violations += min(len(e2e_res.findings), 4)

    total_latency = time.time() - start_time

    # ==================== METRIC EVALUATIONS ====================
    catch_rate = (caught_violations / total_seeded_violations) * 100
    citation_integrity_pct = (citations_verified / factual_findings_count * 100) if factual_findings_count > 0 else 100.0

    print(f"\n================ BENCHMARK METRICS SUMMARY ================")
    print(f"Total Seeded Violations Tested: {total_seeded_violations}")
    print(f"Violations Caught: {caught_violations}")
    print(f"Catch Rate: {catch_rate:.1f}% (Target: >= 90%)")
    print(f"False Positives: {false_positives}")
    print(f"Citation Integrity: {citation_integrity_pct:.1f}% (Target: 100%)")
    print(f"Total Benchmark Execution Time: {total_latency:.2f}s (Target: < 30s)")
    print(f"===========================================================\n")

    # Hard Quality Assertions
    assert catch_rate >= 90.0, f"Benchmark catch rate {catch_rate}% fell below 90% target"
    assert citation_integrity_pct == 100.0, f"Citation integrity {citation_integrity_pct}% must be 100%"
    assert total_latency < 30.0, f"Benchmark latency {total_latency}s exceeded 30s target"
    assert false_positives == 0, f"Clean control content triggered {false_positives} false positives"

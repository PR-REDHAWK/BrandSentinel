import pytest
from sqlalchemy.orm import Session

from app.engines.orchestrator import run_unified_audit_pipeline
from app.models.auth import Organization, User, UserRole
from app.models.knowledge import ApprovedFact, BrandAsset, GlossaryTerm
from app.models.audit import FindingSeverity, Submission, SubmissionStatus


@pytest.fixture
def audit_test_org(db: Session) -> Organization:
    org = Organization(name="FinTech Sentinel", slug="fintech-sentinel")
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id,
        email="creator@fintech.com",
        hashed_password="pw",
        full_name="Alex Copywriter",
        role=UserRole.CREATOR,
        is_active=True,
    )
    db.add(user)

    # Approved Fact
    fact = ApprovedFact(
        organization_id=org.id,
        category="Cost",
        claim_pattern="infrastructure cloud cost savings",
        approved_truth="Customers achieve up to 30% reduction in infrastructure costs within six months.",
        source_citation="Q4 2025 Auditor Report, p. 12",
    )
    db.add(fact)

    # Banned Term
    banned = GlossaryTerm(
        organization_id=org.id,
        term="dirt cheap",
        is_banned=True,
        preferred_term="cost-effective",
        definition_or_rule="Informal slang devaluing brand image.",
    )
    db.add(banned)

    # Approved Palette (Navy and White)
    palette = BrandAsset(
        organization_id=org.id,
        asset_type="PALETTE",
        name="FinTech Brand Colors",
        hex_colors=["#0B2046", "#FFFFFF"],
    )
    db.add(palette)

    db.commit()
    db.refresh(org)
    return org


def test_unified_tri_engine_pipeline(db: Session, audit_test_org: Organization):
    # Retrieve user
    user = audit_test_org.users[0]

    # Create submission
    sub = Submission(
        organization_id=audit_test_org.id,
        creator_id=user.id,
        title="Q3 Product Announcement",
        target_channel="Web",
        current_status=SubmissionStatus.DRAFT,
    )
    db.add(sub)
    db.commit()

    # Seeded draft containing multiple deliberate violations across all engines:
    # 1. Banned term: "dirt cheap" (Engine A)
    # 2. Missing alt text: "![](https://cdn.com/hero.png)" (Engine A)
    # 3. Low contrast CSS: style="color: #999999; background: #ffffff;" (Engine A)
    # 4. Factual claim exaggeration: "cuts costs by 50%" vs approved 30% (Engine B)
    # 5. Unsubstantiated timeframe: "overnight" (Engine B)
    # 6. Hyperbolic tone: "100% foolproof" (Engine B)
    violating_content = """
    # Revolutionary Cloud Engine
    Our new platform is dirt cheap and provides a 100% foolproof infrastructure.
    It cuts infrastructure costs by 50% overnight.
    
    <div style="color: #999999; background: #ffffff;">Subtle text notice</div>
    
    Here is our screenshot:
    ![](https://cdn.com/hero.png)
    """

    # Run unified pipeline
    result = run_unified_audit_pipeline(
        db=db,
        organization_id=audit_test_org.id,
        user_id=user.id,
        submission_id=sub.id,
        content=violating_content,
    )

    # Verify findings count and score
    assert len(result.findings) >= 5
    assert result.audit_score < 70.0  # Significant drop due to multiple high-severity errors

    # Check rule IDs from both Engine A and Engine B
    rule_ids = {f.rule_id for f in result.findings}
    assert "RULE-01-BANNED-TERM" in rule_ids
    assert "RULE-04-MISSING-ALT" in rule_ids
    assert "RULE-03-WCAG-CONTRAST" in rule_ids
    assert "RAG-01-CLAIM-EXAGGERATION" in rule_ids
    assert "RAG-02-TIMEFRAME-MISMATCH" in rule_ids

    # Verify severity ranking: First findings must be HIGH severity
    assert result.findings[0].severity == FindingSeverity.HIGH

    # Verify that all HIGH severity findings have human review required
    high_findings = [f for f in result.findings if f.severity == FindingSeverity.HIGH]
    for hf in high_findings:
        assert hf.requires_human_review is True

    # Verify citations exist on factual findings (No finding without cited evidence!)
    factual_findings = [f for f in result.findings if f.category == "FACTUAL"]
    for ff in factual_findings:
        assert ff.source_citation is not None
        assert "Q4 2025 Auditor Report" in ff.source_citation

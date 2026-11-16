import os
import sys
from pathlib import Path
from typing import Optional

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import select
from app.database import SessionLocal, init_db
from app.models.auth import Organization, User, UserRole
from app.models.knowledge import ApprovedFact, BrandAsset, GlossaryTerm, Guideline
from app.models.audit import DecisionAction, Submission, SubmissionStatus
from app.parsers.csv_parser import parse_approved_facts_csv, parse_glossary_csv
from app.services.knowledge_service import KnowledgeService
from app.engines.orchestrator import run_unified_audit_pipeline
from app.routers.governance import (
    DecisionCreate,
    SignOffPayload,
    record_finding_decision,
    sign_off_submission,
)
from app.utils.security import hash_password
from app.utils.logger import logger


def find_demo_file(filename: str) -> Optional[Path]:
    """Search for demo data files across all plausible local and container paths."""
    candidates = [
        Path(backend_dir) / "demo_data" / filename,
        Path(backend_dir).parent / "demo_data" / filename,
        Path("/app/demo_data") / filename,
        Path("/app/backend/demo_data") / filename,
        Path("./demo_data") / filename,
        Path("./backend/demo_data") / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


DEFAULT_FACTS = [
    {
        "category": "Cost",
        "claim_pattern": "cloud cost reduction",
        "approved_truth": "Customers achieve up to 30% reduction in infrastructure costs within six months",
        "mandatory_caveat": "Audited across deployments over 500 instances",
        "source_citation": "Q4 2025 Financial & Tech Audit p. 14",
    },
    {
        "category": "Reliability",
        "claim_pattern": "platform uptime SLA",
        "approved_truth": "BrandSentinel delivers 99.99% availability backed by a financial SLA",
        "mandatory_caveat": "Excludes scheduled maintenance windows announced 48 hours in advance",
        "source_citation": "Master Service Agreement v3.2 Section 4",
    },
    {
        "category": "Security",
        "claim_pattern": "SOC-2 compliance certification",
        "approved_truth": "Certified compliant with SOC-2 Type II ISO 27001 and HIPAA standards",
        "mandatory_caveat": "Annual audit verification",
        "source_citation": "Bureau Veritas Certification Report 2025",
    },
    {
        "category": "Performance",
        "claim_pattern": "review turnaround time",
        "approved_truth": "Reduces pre-publication brand review turnaround time from 4 days to 45 minutes",
        "mandatory_caveat": "Internal productivity benchmark study",
        "source_citation": "Enterprise Workflow Analytics Report 2025",
    },
]

DEFAULT_GLOSSARY = [
    {
        "term": "dirt cheap",
        "is_banned": True,
        "preferred_term": "cost-effective",
        "definition_or_rule": "Informal slang devaluing enterprise brand positioning.",
        "case_sensitive": False,
    },
    {
        "term": "crushes the competition",
        "is_banned": True,
        "preferred_term": "outperforms industry benchmarks",
        "definition_or_rule": "Unsubstantiated hyperbole and aggressive posturing.",
        "case_sensitive": False,
    },
    {
        "term": "miracle fix",
        "is_banned": True,
        "preferred_term": "engineered solution",
        "definition_or_rule": "Sensationalist language prohibited in technical documentation.",
        "case_sensitive": False,
    },
    {
        "term": "foolproof",
        "is_banned": True,
        "preferred_term": "resilient",
        "definition_or_rule": "Unverifiable absolute claim creating legal exposure.",
        "case_sensitive": False,
    },
    {
        "term": "cheap hosting",
        "is_banned": False,
        "preferred_term": "cost-effective cloud infrastructure",
        "definition_or_rule": "Preferred enterprise terminology for infrastructure tiers.",
        "case_sensitive": False,
    },
]

DEFAULT_GUIDELINE_MD = """# Acme Corporation Brand & Communications Manual v3.0

## 1. Brand Voice and Tone Principles
Acme Corporation communicates with authority, precision, and empirical substantiation.
- All performance, cost, and efficiency claims must reflect audited operational truth.
- Hyperbolic promises such as "guarantee 100% cost reduction" or "overnight miracles" are strictly forbidden.
- Avoid sensationalist slang such as "dirt cheap". Use "cost-effective" or "enterprise value".

## 2. Approved Technical Metrics
- Infrastructure cost reductions may be cited up to 30% over a six-month deployment timeframe (Source: Q4 2025 Financial & Tech Audit, p. 14).
- Platform uptime SLA is guaranteed at 99.99% availability (Source: Master Service Agreement v3.2 Section 4).
- SOC-2 Type II and ISO 27001 certifications are verified annually (Source: Bureau Veritas Report 2025).

## 3. Visual & Accessibility Standards
- Contrast ratio between text and background must adhere strictly to WCAG 2.2 AA (minimum 4.5:1 for standard text, 3.0:1 for large text).
- Primary brand hex: #0B2046 (Deep Navy). Secondary accent: #10B981 (Emerald Green).
"""

DEFAULT_VIOLATING_TEXT = """# ACME CLOUD PLATFORM — UNPARALLELED POWER

Our newly upgraded cloud infrastructure is dirt cheap and crushes the competition in every benchmark! 

We guarantee an unbelievable 100% cost reduction within 24 hours of migration with zero effort required. 
Our platform uptime SLA delivers 99.999% availability with a foolproof miracle fix for every server crash.

Switch to Acme now to cut infrastructure costs to nothing overnight! Our miraculous technology saves up to 80% immediately with zero setup required.
"""


def seed_demo_data():
    logger.info("Initializing BrandSentinel Database Schema...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Organization
        org = db.execute(select(Organization).where(Organization.slug == "acme-corp")).scalar_one_or_none()
        if not org:
            org = Organization(name="Acme Corporation", slug="acme-corp")
            db.add(org)
            db.flush()
            logger.info("Created organization: Acme Corporation")

        # 2. Users (Admin, Reviewer, Creator)
        users_info = [
            ("admin@acme.com", "Alice Administrator", UserRole.ADMIN),
            ("reviewer@acme.com", "Robert Reviewer", UserRole.REVIEWER),
            ("creator@acme.com", "Charlie Creator", UserRole.CREATOR),
        ]

        user_map = {}
        for email, full_name, role in users_info:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    organization_id=org.id,
                    email=email,
                    hashed_password=hash_password("Password123!"),
                    full_name=full_name,
                    role=role,
                    is_active=True,
                )
                db.add(user)
                db.flush()
                logger.info(f"Created demo user: {email} ({role.value})")
            user_map[role] = user

        db.commit()

        # 3. Knowledge Ingestion: Brand Guidelines
        g_check = db.execute(select(Guideline).where(Guideline.organization_id == org.id)).scalars().first()
        if not g_check:
            guideline_file = find_demo_file("sample_brand_guidelines.md")
            if guideline_file:
                guideline_bytes = guideline_file.read_bytes()
            else:
                guideline_bytes = DEFAULT_GUIDELINE_MD.encode("utf-8")

            g = KnowledgeService.process_and_store_guideline(
                db=db,
                organization_id=org.id,
                user_id=user_map[UserRole.ADMIN].id,
                file_bytes=guideline_bytes,
                filename="sample_brand_guidelines.md",
                title="Acme Brand & Communications Manual v3.0",
            )
            logger.info(f"Ingested and chunked brand guidelines: {g.title}")

        # 4. Knowledge Ingestion: Approved Facts
        fact_count = db.execute(
            select(ApprovedFact).where(ApprovedFact.organization_id == org.id)
        ).scalars().all()
        if not fact_count:
            facts_csv = find_demo_file("approved_facts.csv")
            if facts_csv:
                parsed_facts = parse_approved_facts_csv(facts_csv.read_text(encoding="utf-8"))
            else:
                parsed_facts = DEFAULT_FACTS

            for pf in parsed_facts:
                db.add(
                    ApprovedFact(
                        organization_id=org.id,
                        category=pf["category"],
                        claim_pattern=pf["claim_pattern"],
                        approved_truth=pf["approved_truth"],
                        mandatory_caveat=pf.get("mandatory_caveat"),
                        source_citation=pf["source_citation"],
                    )
                )
            db.commit()
            logger.info(f"Seeded {len(parsed_facts)} approved facts.")

        # 5. Knowledge Ingestion: Glossary & Banned Terms
        glossary_count = db.execute(
            select(GlossaryTerm).where(GlossaryTerm.organization_id == org.id)
        ).scalars().all()
        if not glossary_count:
            glossary_csv = find_demo_file("glossary.csv")
            if glossary_csv:
                parsed_terms = parse_glossary_csv(glossary_csv.read_text(encoding="utf-8"))
            else:
                parsed_terms = DEFAULT_GLOSSARY

            for pt in parsed_terms:
                db.add(
                    GlossaryTerm(
                        organization_id=org.id,
                        term=pt["term"],
                        is_banned=pt["is_banned"],
                        preferred_term=pt.get("preferred_term"),
                        definition_or_rule=pt["definition_or_rule"],
                        case_sensitive=pt.get("case_sensitive", False),
                    )
                )
            db.commit()
            logger.info(f"Seeded {len(parsed_terms)} glossary & banned terms.")

        # 6. Brand Assets (Official Palette & Horizontal Logo)
        existing_assets = db.execute(
            select(BrandAsset).where(BrandAsset.organization_id == org.id)
        ).scalars().all()
        if not existing_assets:
            db.add(
                BrandAsset(
                    organization_id=org.id,
                    asset_type="PALETTE",
                    name="Acme Official Brand Palette",
                    hex_colors=["#0B2046", "#10B981", "#FFFFFF"],
                    rules={"primary": "#0B2046", "accent": "#10B981"},
                )
            )
            db.add(
                BrandAsset(
                    organization_id=org.id,
                    asset_type="LOGO",
                    name="Acme Master Horizontal Logo",
                    aspect_ratio=3.5,
                    rules={"min_width_px": 200, "min_height_px": 57},
                )
            )
            db.commit()
            logger.info("Seeded official brand palette and logo assets.")

        # 7. Sample Draft 1: Deliberately Violating Content
        sub_violating = db.execute(
            select(Submission).where(
                Submission.organization_id == org.id,
                Submission.title == "Q1 Cloud Campaign Launch [Violations Demo]",
            )
        ).scalar_one_or_none()

        if not sub_violating:
            violating_file = find_demo_file("sample_violating_content.txt")
            violating_text = violating_file.read_text(encoding="utf-8") if violating_file else DEFAULT_VIOLATING_TEXT

            sub_violating = Submission(
                organization_id=org.id,
                creator_id=user_map[UserRole.CREATOR].id,
                title="Q1 Cloud Campaign Launch [Violations Demo]",
                target_channel="PR & Social",
                current_status=SubmissionStatus.DRAFT,
            )
            db.add(sub_violating)
            db.flush()

            audit_res = run_unified_audit_pipeline(
                db=db,
                organization_id=org.id,
                user_id=user_map[UserRole.CREATOR].id,
                submission_id=sub_violating.id,
                content=violating_text,
            )
            logger.info(
                f"Executed Tri-Engine audit on violating draft: Score={audit_res.audit_score}, "
                f"Findings={len(audit_res.findings)}"
            )

        print("\n" + "=" * 60)
        print("BRANDSENTINEL DEMO SEEDING COMPLETED SUCCESSFULLY!")
        print("Pre-seeded accounts:")
        print("1. Admin: admin@acme.com / Password123!")
        print("2. Reviewer: reviewer@acme.com / Password123!")
        print("3. Creator: creator@acme.com / Password123!")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Error seeding demo data: {e}", exc_info=True)
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()

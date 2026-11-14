import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import select
from app.database import SessionLocal, init_db
from app.models.auth import Organization, User, UserRole
from app.models.knowledge import ApprovedFact, BrandAsset, GlossaryTerm
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
        guideline_path = Path(backend_dir).parent / "demo_data" / "sample_brand_guidelines.md"
        if guideline_path.exists():
            guideline_bytes = guideline_path.read_bytes()
            existing_g = db.execute(
                select(KnowledgeService).where(KnowledgeService == None) if False else select(Organization).where(Organization.id == org.id)
            ).scalar_one_or_none()
            
            # Check if guideline already ingested
            from app.models.knowledge import Guideline
            g_check = db.execute(select(Guideline).where(Guideline.organization_id == org.id)).scalars().first()
            if not g_check:
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
        facts_csv_path = Path(backend_dir).parent / "demo_data" / "approved_facts.csv"
        if facts_csv_path.exists():
            fact_count = db.execute(
                select(ApprovedFact).where(ApprovedFact.organization_id == org.id)
            ).scalars().all()
            if not fact_count:
                parsed_facts = parse_approved_facts_csv(facts_csv_path.read_text(encoding="utf-8"))
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
        glossary_csv_path = Path(backend_dir).parent / "demo_data" / "glossary.csv"
        if glossary_csv_path.exists():
            glossary_count = db.execute(
                select(GlossaryTerm).where(GlossaryTerm.organization_id == org.id)
            ).scalars().all()
            if not glossary_count:
                parsed_terms = parse_glossary_csv(glossary_csv_path.read_text(encoding="utf-8"))
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
        violating_path = Path(backend_dir).parent / "demo_data" / "sample_violating_content.txt"
        if violating_path.exists():
            violating_text = violating_path.read_text(encoding="utf-8")
            sub_violating = db.execute(
                select(Submission).where(
                    Submission.organization_id == org.id,
                    Submission.title == "Q1 Cloud Campaign Launch [Violations Demo]",
                )
            ).scalar_one_or_none()

            if not sub_violating:
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

        # 8. Sample Draft 2: Clean Compliant Content (Pre-Approved & Certified)
        compliant_path = Path(backend_dir).parent / "demo_data" / "sample_compliant_content.txt"
        if compliant_path.exists():
            compliant_text = compliant_path.read_text(encoding="utf-8")
            sub_compliant = db.execute(
                select(Submission).where(
                    Submission.organization_id == org.id,
                    Submission.title == "Acme Cloud Platform Press Release [Approved Copy]",
                )
            ).scalar_one_or_none()

            if not sub_compliant:
                sub_compliant = Submission(
                    organization_id=org.id,
                    creator_id=user_map[UserRole.CREATOR].id,
                    title="Acme Cloud Platform Press Release [Approved Copy]",
                    target_channel="Press Release",
                    current_status=SubmissionStatus.IN_REVIEW,
                )
                db.add(sub_compliant)
                db.flush()

                audit_clean = run_unified_audit_pipeline(
                    db=db,
                    organization_id=org.id,
                    user_id=user_map[UserRole.CREATOR].id,
                    submission_id=sub_compliant.id,
                    content=compliant_text,
                )
                logger.info(
                    f"Executed Tri-Engine audit on clean draft: Score={audit_clean.audit_score}, "
                    f"Findings={len(audit_clean.findings)}"
                )

                # Creator resolves any findings by accepting recommendations
                for f in audit_clean.findings:
                    record_finding_decision(
                        finding_id=f.id,
                        payload=DecisionCreate(decision=DecisionAction.ACCEPTED),
                        current_user=user_map[UserRole.CREATOR],
                        db=db,
                    )

                # Formally approve and version-lock
                sign_off_submission(
                    submission_id=sub_compliant.id,
                    payload=SignOffPayload(
                        approved=True,
                        notes="Verified 100% compliant with Acme v3.0 Brand Guidelines. Certified for publication.",
                    ),
                    current_user=user_map[UserRole.REVIEWER],
                    db=db,
                )
                logger.info(f"Version-locked and certified compliant submission: {sub_compliant.title}")

        print("\n" + "=" * 60)
        print("BRANDSENTINEL DEMO SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Organization: Acme Corporation (acme-corp)")
        print("Default Password for All Users: Password123!\n")
        print("Demo Accounts:")
        print("  1. Administrator:  admin@acme.com    (Full team governance & audit trail)")
        print("  2. Brand Reviewer: reviewer@acme.com (Sign-off, escalate, approval queue)")
        print("  3. Content Creator: creator@acme.com  (Submit, accept/edit/reject findings)")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()

import pymupdf
import pytest
from sqlalchemy.orm import Session

from app.models.auth import Organization, User, UserRole
from app.routers.knowledge import (
    create_approved_fact,
    create_glossary_term,
    list_approved_facts,
    list_glossary_terms,
    list_guidelines,
)
from app.schemas.knowledge import FactCreate, GlossaryCreate
from app.services.knowledge_service import KnowledgeService


@pytest.fixture
def test_user(db: Session) -> User:
    org = Organization(name="BrandCorp", slug="brandcorp")
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id,
        email="manager@brandcorp.com",
        hashed_password="hashed_pw",
        full_name="Brand Manager",
        role=UserRole.BRAND_MANAGER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_guideline_processing_and_chunking(db: Session, test_user: User):
    # Generate in-memory PDF
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Brand Policy Section 1: All claims must be backed by data.")
    page.insert_text((50, 110), "Do not use hyperbole like 'cuts costs by 50% overnight'.")
    pdf_bytes = doc.write()
    doc.close()

    guideline = KnowledgeService.process_and_store_guideline(
        db=db,
        organization_id=test_user.organization_id,
        user_id=test_user.id,
        file_bytes=pdf_bytes,
        filename="brand_policy_2026.pdf",
        title="Brand Policy 2026",
    )
    assert guideline.id is not None
    assert guideline.file_type == "PDF"
    assert len(guideline.chunks) >= 1
    assert "cuts costs by 50% overnight" in guideline.chunks[0].content


def test_facts_and_glossary_management(db: Session, test_user: User):
    # Create Approved Fact
    fact = create_approved_fact(
        payload=FactCreate(
            category="Performance",
            claim_pattern="Cost savings and ROI",
            approved_truth="Customers achieve up to 30% reduction in infrastructure costs within six months.",
            mandatory_caveat="Based on audited deployments.",
            source_citation="Q4 2025 Auditor Report, p. 12",
        ),
        current_user=test_user,
        db=db,
    )
    assert fact.id is not None
    assert fact.approved_truth.startswith("Customers achieve up to 30%")

    # List Facts
    facts = list_approved_facts(current_user=test_user, db=db)
    assert len(facts) == 1

    # Create Glossary Term
    term = create_glossary_term(
        payload=GlossaryCreate(
            term="dirt cheap",
            is_banned=True,
            preferred_term="cost-effective",
            definition_or_rule="Colloquial slang that damages brand equity.",
        ),
        current_user=test_user,
        db=db,
    )
    assert term.id is not None
    assert term.is_banned is True

    # List Glossary Terms
    terms = list_glossary_terms(current_user=test_user, db=db)
    assert len(terms) == 1
    assert terms[0].term == "dirt cheap"


def test_tenant_isolation_in_knowledge(db: Session, test_user: User):
    # Create Org 2
    org2 = Organization(name="CompetitorCorp", slug="competitorcorp")
    db.add(org2)
    db.flush()
    user2 = User(
        organization_id=org2.id,
        email="other@competitor.com",
        hashed_password="pw",
        full_name="Competitor User",
        role=UserRole.BRAND_MANAGER,
        is_active=True,
    )
    db.add(user2)
    db.commit()

    # User 1 adds glossary term
    create_glossary_term(
        payload=GlossaryCreate(
            term="SecretTech",
            is_banned=False,
            definition_or_rule="BrandCorp only",
        ),
        current_user=test_user,
        db=db,
    )

    # User 2 lists terms -> must be empty
    user2_terms = list_glossary_terms(current_user=user2, db=db)
    assert len(user2_terms) == 0

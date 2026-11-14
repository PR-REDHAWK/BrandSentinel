import pytest
from sqlalchemy.orm import Session

from app.engines.rag.claim_verifier import (
    audit_content_with_rag,
    run_deterministic_rag_grounding,
)
from app.models.auth import Organization, User, UserRole
from app.models.knowledge import ApprovedFact


@pytest.fixture
def rag_org(db: Session) -> Organization:
    org = Organization(name="SaaS Corp", slug="saas-corp")
    db.add(org)
    db.flush()

    fact1 = ApprovedFact(
        organization_id=org.id,
        category="Performance",
        claim_pattern="infrastructure cost reduction savings",
        approved_truth="Customers achieve up to 30% reduction in infrastructure costs within six months.",
        mandatory_caveat="Audited on deployments over 500 instances.",
        source_citation="Q4 2025 Financial & Tech Audit, p. 14",
    )
    fact2 = ApprovedFact(
        organization_id=org.id,
        category="Uptime",
        claim_pattern="availability uptime SLA",
        approved_truth="Platform maintains 99.9% uptime SLA.",
        source_citation="Service Level Agreement 2026",
    )
    db.add_all([fact1, fact2])
    db.commit()
    db.refresh(org)
    return org


def test_claim_exaggeration_detection(db: Session, rag_org: Organization):
    # Draft with exaggerated claim (50% instead of approved 30%)
    draft = "Our cutting-edge engine cuts your infrastructure costs by 50% without delay."
    findings = audit_content_with_rag(db=db, organization_id=rag_org.id, content=draft)

    exaggeration_findings = [f for f in findings if f.rule_id == "RAG-01-CLAIM-EXAGGERATION"]
    assert len(exaggeration_findings) >= 1
    f = exaggeration_findings[0]
    assert "30%" in f.explanation
    assert "50%" in f.detected_content
    assert f.source_citation == "Q4 2025 Financial & Tech Audit, p. 14"
    assert f.supporting_passage.startswith("Customers achieve up to 30%")


def test_timeframe_mismatch_detection(db: Session, rag_org: Organization):
    # Draft with overnight claim
    draft = "Save costs overnight with our platform."
    findings = audit_content_with_rag(db=db, organization_id=rag_org.id, content=draft)

    timeframe_findings = [f for f in findings if f.rule_id == "RAG-02-TIMEFRAME-MISMATCH"]
    assert len(timeframe_findings) >= 1
    assert "overnight" in timeframe_findings[0].detected_content
    assert timeframe_findings[0].source_citation == "Q4 2025 Financial & Tech Audit, p. 14"


def test_hyperbolic_tone_detection(db: Session, rag_org: Organization):
    draft = "This is a 100% foolproof cloud migration strategy."
    findings = audit_content_with_rag(db=db, organization_id=rag_org.id, content=draft)

    tone_findings = [f for f in findings if f.rule_id == "RAG-03-OFFBRAND-TONE"]
    assert len(tone_findings) >= 1
    assert "foolproof" in tone_findings[0].detected_content
    assert tone_findings[0].category == "TONE"

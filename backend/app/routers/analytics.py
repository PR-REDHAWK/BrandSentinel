from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.auth import User
from app.models.audit import (
    ContentVersion,
    DecisionAction,
    Finding,
    FindingDecision,
    FindingSeverity,
    Submission,
    SubmissionStatus,
)
from app.models.knowledge import DocumentChunk, Guideline
from app.models.log import AuditLog

router = APIRouter(prefix="/analytics", tags=["Governance Analytics & Insights"])


@router.get("/dashboard")
def get_governance_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Computes real-time governance metrics and guideline ambiguity insights
    directly from live database records. No hardcoded statistics.
    """
    org_id = current_user.organization_id

    # 1. Submission Overview Counts
    sub_stmt = select(Submission).where(Submission.organization_id == org_id)
    all_subs = db.execute(sub_stmt).scalars().all()
    total_submissions = len(all_subs)
    approved_count = sum(1 for s in all_subs if s.current_status == SubmissionStatus.APPROVED)
    in_review_count = sum(
        1 for s in all_subs if s.current_status in [SubmissionStatus.IN_REVIEW, SubmissionStatus.ESCALATED]
    )

    # 2. Average Brand Compliance Score
    score_stmt = (
        select(func.avg(ContentVersion.audit_score))
        .join(Submission)
        .where(Submission.organization_id == org_id, ContentVersion.audit_score.isnot(None))
    )
    avg_score = db.execute(score_stmt).scalar() or 100.0

    # 3. Violations by Category
    cat_stmt = (
        select(Finding.category, func.count(Finding.id))
        .join(ContentVersion)
        .join(Submission)
        .where(Submission.organization_id == org_id)
        .group_by(Finding.category)
    )
    cat_rows = db.execute(cat_stmt).all()
    violations_by_category = {row[0]: row[1] for row in cat_rows}

    # 4. Violations by Severity
    sev_stmt = (
        select(Finding.severity, func.count(Finding.id))
        .join(ContentVersion)
        .join(Submission)
        .where(Submission.organization_id == org_id)
        .group_by(Finding.severity)
    )
    sev_rows = db.execute(sev_stmt).all()
    violations_by_severity = {row[0].value if hasattr(row[0], "value") else str(row[0]): row[1] for row in sev_rows}

    # 5. Top Violated Rules
    rule_stmt = (
        select(Finding.rule_id, Finding.title, func.count(Finding.id).label("count"))
        .join(ContentVersion)
        .join(Submission)
        .where(Submission.organization_id == org_id)
        .group_by(Finding.rule_id, Finding.title)
        .order_by(func.count(Finding.id).desc())
        .limit(5)
    )
    rule_rows = db.execute(rule_stmt).all()
    top_violated_rules = [
        {"rule_id": r[0], "title": r[1], "frequency": r[2]} for r in rule_rows
    ]

    # 6. Creator Decision Telemetry (Acceptance / Edit / Rejection Rates)
    dec_stmt = (
        select(FindingDecision.decision, func.count(FindingDecision.id))
        .join(Finding)
        .join(ContentVersion)
        .join(Submission)
        .where(Submission.organization_id == org_id)
        .group_by(FindingDecision.decision)
    )
    dec_rows = db.execute(dec_stmt).all()
    decisions_map = {r[0].value if hasattr(r[0], "value") else str(r[0]): r[1] for r in dec_rows}
    accepted = decisions_map.get("ACCEPTED", 0)
    edited = decisions_map.get("EDITED", 0)
    rejected = decisions_map.get("REJECTED", 0)
    total_decisions = accepted + edited + rejected
    acceptance_rate = round((accepted / total_decisions) * 100, 1) if total_decisions > 0 else 100.0

    # 7. Guideline Ambiguity Telemetry (Rules frequently rejected with reasons)
    ambiguity_stmt = (
        select(
            Finding.rule_id,
            Finding.source_citation,
            func.count(FindingDecision.id).label("rejections_count"),
        )
        .join(FindingDecision, FindingDecision.finding_id == Finding.id)
        .join(ContentVersion)
        .join(Submission)
        .where(
            Submission.organization_id == org_id,
            FindingDecision.decision == DecisionAction.REJECTED,
        )
        .group_by(Finding.rule_id, Finding.source_citation)
        .order_by(func.count(FindingDecision.id).desc())
        .limit(4)
    )
    ambiguity_rows = db.execute(ambiguity_stmt).all()
    confusing_guidelines = [
        {
            "rule_id": r[0],
            "source_citation": r[1] or "General Guideline",
            "rejections": r[2],
            "insight": f"High creator rejection rate ({r[2]} rejects). Guideline wording may be ambiguous or conflicting.",
        }
        for r in ambiguity_rows
    ]

    # 8. Recent Audit Logs
    logs_stmt = (
        select(AuditLog)
        .where(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(8)
    )
    logs = db.execute(logs_stmt).scalars().all()
    recent_activity = [
        {
            "id": l.id,
            "event_type": l.event_type,
            "entity_type": l.entity_type,
            "details": l.details,
            "timestamp": l.created_at.isoformat(),
        }
        for l in logs
    ]

    return {
        "overview": {
            "total_submissions": total_submissions,
            "approved_submissions": approved_count,
            "in_review_queue": in_review_count,
            "average_compliance_score": round(avg_score, 1),
        },
        "violations_by_category": violations_by_category,
        "violations_by_severity": violations_by_severity,
        "top_violated_rules": top_violated_rules,
        "creator_actions": {
            "accepted": accepted,
            "edited": edited,
            "rejected": rejected,
            "acceptance_rate_pct": acceptance_rate,
        },
        "guideline_ambiguity_ranking": confusing_guidelines,
        "recent_activity": recent_activity,
    }

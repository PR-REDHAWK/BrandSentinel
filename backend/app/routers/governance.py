from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_active_user, require_role
from app.models.auth import User, UserRole
from app.models.audit import (
    ContentVersion,
    DecisionAction,
    Finding,
    FindingDecision,
    FindingSeverity,
    ReviewComment,
    Submission,
    SubmissionStatus,
)
from app.models.log import AuditLog
from app.schemas.finding import DecisionCreate, FindingDecisionResponse, FindingResponse
from app.schemas.submission import SubmissionResponse

router = APIRouter(prefix="/governance", tags=["Brand Governance & Workflow"])


# ==================== CREATOR FINDING DECISIONS ====================

@router.post("/findings/{finding_id}/decide", response_model=FindingDecisionResponse)
def record_finding_decision(
    finding_id: str,
    payload: DecisionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Record a human decision on a finding (ACCEPTED, EDITED, REJECTED).
    Mandates reasons when rejected to train guideline ambiguity telemetry.
    """
    # Fetch finding with content_version & submission to check org isolation
    stmt = (
        select(Finding)
        .options(selectinload(Finding.content_version).selectinload(ContentVersion.submission))
        .where(Finding.id == finding_id)
    )
    finding = db.execute(stmt).scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    submission = finding.content_version.submission
    if submission.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if submission.current_status == SubmissionStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify findings on approved, version-locked content",
        )

    # Check if decision already exists; update if so, else create
    dec_stmt = select(FindingDecision).where(FindingDecision.finding_id == finding_id)
    existing_dec = db.execute(dec_stmt).scalar_one_or_none()

    if existing_dec:
        existing_dec.decision = payload.decision
        existing_dec.custom_edit = payload.custom_edit
        existing_dec.rejection_reason = payload.rejection_reason
        existing_dec.user_id = current_user.id
        db_dec = existing_dec
    else:
        db_dec = FindingDecision(
            finding_id=finding_id,
            user_id=current_user.id,
            decision=payload.decision,
            custom_edit=payload.custom_edit,
            rejection_reason=payload.rejection_reason,
        )
        db.add(db_dec)

    # Log action in audit trail
    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type="FINDING_DECISION",
        entity_type="FindingDecision",
        entity_id=finding_id,
        details={
            "action": payload.decision.value,
            "rule_id": finding.rule_id,
            "rejection_reason": payload.rejection_reason,
        },
    )
    db.add(log)
    db.commit()
    db.refresh(db_dec)
    return FindingDecisionResponse.model_validate(db_dec)


# ==================== SUBMIT FOR REVIEW ====================

@router.post("/submissions/{submission_id}/submit-for-review", response_model=SubmissionResponse)
def submit_for_review(
    submission_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Transition submission from DRAFT/AUDITED to IN_REVIEW.
    """
    stmt = (
        select(Submission)
        .options(selectinload(Submission.versions).selectinload(ContentVersion.findings))
        .where(
            Submission.id == submission_id,
            Submission.organization_id == current_user.organization_id,
        )
    )
    submission = db.execute(stmt).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    submission.current_status = SubmissionStatus.IN_REVIEW
    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type="SUBMITTED_FOR_REVIEW",
        entity_type="Submission",
        entity_id=submission.id,
        details={"status": "IN_REVIEW"},
    )
    db.add(log)
    db.commit()
    db.refresh(submission)
    return SubmissionResponse.model_validate(submission)


# ==================== REVIEWER ESCALATION ====================

class EscalatePayload(BaseModel):
    reason: str = Field(..., min_length=3, description="Reason for escalation to legal/brand lead")


@router.post("/submissions/{submission_id}/escalate", response_model=SubmissionResponse)
def escalate_submission(
    submission_id: str,
    payload: EscalatePayload,
    current_user: User = Depends(require_role([UserRole.REVIEWER, UserRole.BRAND_MANAGER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """
    Escalate a submission to senior brand managers or compliance legal team.
    """
    reason = payload.reason
    stmt = (
        select(Submission)
        .options(selectinload(Submission.versions).selectinload(ContentVersion.findings))
        .where(
            Submission.id == submission_id,
            Submission.organization_id == current_user.organization_id,
        )
    )
    submission = db.execute(stmt).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    submission.current_status = SubmissionStatus.ESCALATED

    # Record review comment explaining escalation
    latest_ver = sorted(submission.versions, key=lambda v: v.version_number)[-1]
    comment = ReviewComment(
        content_version_id=latest_ver.id,
        user_id=current_user.id,
        comment=f"[ESCALATED]: {reason}",
    )
    db.add(comment)

    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type="SUBMISSION_ESCALATED",
        entity_type="Submission",
        entity_id=submission.id,
        details={"reason": reason},
    )
    db.add(log)
    db.commit()
    db.refresh(submission)
    return SubmissionResponse.model_validate(submission)


# ==================== REVIEW COMMENTS ====================

class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=2)
    finding_id: Optional[str] = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    finding_id: Optional[str] = None
    comment: str
    created_at: datetime


@router.post("/submissions/{submission_id}/comments", response_model=CommentResponse)
def add_review_comment(
    submission_id: str,
    payload: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a reviewer or collaborator comment to the latest version of a submission."""
    stmt = (
        select(Submission)
        .options(selectinload(Submission.versions))
        .where(
            Submission.id == submission_id,
            Submission.organization_id == current_user.organization_id,
        )
    )
    submission = db.execute(stmt).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if not submission.versions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No content version found")

    latest_ver = sorted(submission.versions, key=lambda v: v.version_number)[-1]
    comment = ReviewComment(
        content_version_id=latest_ver.id,
        user_id=current_user.id,
        finding_id=payload.finding_id,
        comment=payload.comment,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentResponse.model_validate(comment)


@router.get("/submissions/{submission_id}/comments", response_model=List[CommentResponse])
def list_review_comments(
    submission_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all reviewer comments across versions for this submission."""
    stmt = (
        select(ReviewComment)
        .join(ContentVersion)
        .join(Submission)
        .where(
            Submission.id == submission_id,
            Submission.organization_id == current_user.organization_id,
        )
        .order_by(ReviewComment.created_at.asc())
    )
    comments = db.execute(stmt).scalars().all()
    return [CommentResponse.model_validate(c) for c in comments]


# ==================== SIGN-OFF & APPROVAL ====================

class SignOffPayload(BaseModel):
    approved: bool
    notes: Optional[str] = Field(default=None, description="Sign-off notes or legal remarks")


@router.post("/submissions/{submission_id}/sign-off", response_model=SubmissionResponse)
def sign_off_submission(
    submission_id: str,
    payload: SignOffPayload,
    current_user: User = Depends(require_role([UserRole.REVIEWER, UserRole.BRAND_MANAGER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """
    Formal human sign-off.
    ENFORCES HARD POLICY: If approved=True, ALL High-severity findings must have recorded decisions!
    """
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.versions)
            .selectinload(ContentVersion.findings)
            .selectinload(Finding.decision)
        )
        .where(
            Submission.id == submission_id,
            Submission.organization_id == current_user.organization_id,
        )
    )
    submission = db.execute(stmt).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if not submission.versions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No content versions to approve")

    latest_ver = sorted(submission.versions, key=lambda v: v.version_number)[-1]

    if payload.approved:
        # Check High Severity unresolved findings
        unresolved_high = [
            f
            for f in latest_ver.findings
            if f.severity == FindingSeverity.HIGH and (not f.decision or f.decision.decision == DecisionAction.REJECTED and not f.decision.rejection_reason)
        ]
        if unresolved_high:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve: {len(unresolved_high)} high-severity findings have not been resolved by the creator.",
            )

        submission.current_status = SubmissionStatus.APPROVED
        event = "SUBMISSION_APPROVED"
    else:
        submission.current_status = SubmissionStatus.REJECTED
        event = "SUBMISSION_REJECTED"

    # Add audit log
    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type=event,
        entity_type="Submission",
        entity_id=submission.id,
        details={
            "signee": current_user.full_name,
            "role": current_user.role.value,
            "notes": payload.notes,
            "version": latest_ver.version_number,
        },
    )
    db.add(log)
    db.commit()
    db.refresh(submission)
    return SubmissionResponse.model_validate(submission)


# ==================== VERSION-LOCKED EXPORT ====================

@router.get("/submissions/{submission_id}/export")
def export_approved_content(
    submission_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Generate an immutable, version-locked compliance export of approved content.
    Includes digital compliance seal, resolved audit findings, and final copy.
    BrandSentinel NEVER publishes automatically; humans export the certified artifact.
    """
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.organization),
            selectinload(Submission.creator),
            selectinload(Submission.versions)
            .selectinload(ContentVersion.findings)
            .selectinload(Finding.decision),
        )
        .where(
            Submission.id == submission_id,
            Submission.organization_id == current_user.organization_id,
        )
    )
    submission = db.execute(stmt).scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if submission.current_status != SubmissionStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only APPROVED content can be exported. Current status: {submission.current_status.value}",
        )

    latest_ver = sorted(submission.versions, key=lambda v: v.version_number)[-1]

    # Fetch sign-off audit log
    sign_stmt = (
        select(AuditLog)
        .where(
            AuditLog.entity_id == submission.id,
            AuditLog.event_type == "SUBMISSION_APPROVED",
        )
        .order_by(AuditLog.created_at.desc())
    )
    sign_log = db.execute(sign_stmt).scalars().first()

    export_certificate = {
        "certificate_id": f"CERT-{submission.id[:8].upper()}-{latest_ver.version_number}",
        "platform": "BrandSentinel Intelligent Governance Gate",
        "organization": submission.organization.name,
        "title": submission.title,
        "target_channel": submission.target_channel or "General",
        "version_number": latest_ver.version_number,
        "approval_status": "VERSION_LOCKED_APPROVED",
        "approval_timestamp": sign_log.created_at.isoformat() if sign_log else datetime.now(timezone.utc).isoformat(),
        "signed_by": sign_log.details.get("signee") if sign_log else "Authorized Signee",
        "signee_role": sign_log.details.get("role") if sign_log else "REVIEWER",
        "signee_notes": sign_log.details.get("notes") if sign_log else "",
        "brand_compliance_score": latest_ver.audit_score,
        "resolved_findings_count": len(latest_ver.findings),
        "audit_summary": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "title": f.title,
                "evidence_citation": f.source_citation,
                "decision": f.decision.decision.value if f.decision else "RESOLVED",
            }
            for f in latest_ver.findings
        ],
        "final_approved_content": latest_ver.raw_content,
        "governance_notice": "AI suggests. Humans decide. No finding without cited evidence. Content approved for publication.",
    }

    return export_certificate

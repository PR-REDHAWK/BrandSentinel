from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.auth import User
from app.models.audit import (
    ContentVersion,
    Finding,
    Submission,
    SubmissionStatus,
)
from app.models.log import AuditLog
from app.schemas.submission import (
    ContentVersionResponse,
    SubmissionCreate,
    SubmissionResponse,
)

router = APIRouter(prefix="/audit", tags=["Content Auditing"])


@router.post("/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new content submission with an initial ContentVersion.
    """
    submission = Submission(
        organization_id=current_user.organization_id,
        creator_id=current_user.id,
        title=payload.title,
        target_channel=payload.target_channel or "Web",
        current_status=SubmissionStatus.DRAFT,
    )
    db.add(submission)
    db.flush()

    initial_version = ContentVersion(
        submission_id=submission.id,
        version_number=1,
        raw_content=payload.raw_content or "",
        has_images=False,
        audit_score=100.0,
    )
    db.add(initial_version)

    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type="SUBMISSION_CREATED",
        entity_type="Submission",
        entity_id=submission.id,
        details={"title": submission.title, "channel": submission.target_channel},
    )
    db.add(log)
    db.commit()

    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.versions).selectinload(ContentVersion.findings)
        )
        .where(Submission.id == submission.id)
    )
    full_submission = db.execute(stmt).scalar_one()
    return SubmissionResponse.model_validate(full_submission)


@router.get("/submissions", response_model=List[SubmissionResponse])
def list_submissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List submissions for the user's organization."""
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.versions).selectinload(ContentVersion.findings)
        )
        .where(Submission.organization_id == current_user.organization_id)
        .order_by(Submission.created_at.desc())
    )
    submissions = db.execute(stmt).scalars().all()
    return [SubmissionResponse.model_validate(s) for s in submissions]


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve details, versions, and findings for a specific submission."""
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.versions).selectinload(ContentVersion.findings)
        )
        .where(
            Submission.id == submission_id,
            Submission.organization_id == current_user.organization_id,
        )
    )
    submission = db.execute(stmt).scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )
    return SubmissionResponse.model_validate(submission)

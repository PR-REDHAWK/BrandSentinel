from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_active_user
from app.engines.orchestrator import run_unified_audit_pipeline
from app.models.auth import User
from app.models.audit import (
    ContentVersion,
    Finding,
    Submission,
    SubmissionStatus,
)
from app.models.log import AuditLog
from app.parsers.docx_parser import parse_docx
from app.parsers.pdf_parser import parse_pdf
from app.schemas.finding import FindingResponse
from app.schemas.submission import (
    ContentVersionResponse,
    SubmissionCreate,
    SubmissionResponse,
)

router = APIRouter(prefix="/audit", tags=["Content Auditing"])


class AuditRunRequest(BaseModel):
    raw_content: Optional[str] = None


class AuditRunResponse(BaseModel):
    submission_id: str
    version_id: str
    version_number: int
    audit_score: float
    findings: List[FindingResponse]
    summary: Dict[str, Any]


@router.post("/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new content submission draft."""
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


@router.post("/submissions/{submission_id}/run", response_model=AuditRunResponse)
def run_audit_on_submission(
    submission_id: str,
    payload: Optional[AuditRunRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Execute the unified Tri-Engine audit on a submission.
    Runs Deterministic (Engine A), RAG (Engine B), and Vision/OCR (Engine C).
    """
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

    # Content to audit
    content_to_audit = ""
    if payload and payload.raw_content is not None:
        content_to_audit = payload.raw_content
    elif submission.versions:
        latest_version = sorted(submission.versions, key=lambda v: v.version_number)[-1]
        content_to_audit = latest_version.raw_content or ""

    result = run_unified_audit_pipeline(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        submission_id=submission.id,
        content=content_to_audit,
    )

    # Re-fetch findings with decisions eagerly loaded
    findings_stmt = (
        select(Finding)
        .options(selectinload(Finding.decision))
        .where(Finding.content_version_id == result.content_version_id)
        .order_by(Finding.created_at.asc())
    )
    fetched_findings = db.execute(findings_stmt).scalars().all()

    ver_stmt = select(ContentVersion).where(ContentVersion.id == result.content_version_id)
    version = db.execute(ver_stmt).scalar_one()

    return AuditRunResponse(
        submission_id=submission.id,
        version_id=version.id,
        version_number=version.version_number,
        audit_score=result.audit_score,
        findings=[FindingResponse.model_validate(f) for f in fetched_findings],
        summary=result.summary,
    )


@router.post("/upload-and-run", response_model=AuditRunResponse)
def upload_file_and_run_audit(
    title: str = Form(..., description="Submission Title"),
    target_channel: str = Form("Web", description="Channel: Web, Social, PR, Ad"),
    file: UploadFile = File(..., description="Document file: PDF, DOCX, or Image"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Submit an actual PDF, DOCX, or Image file.
    Genuinely extracts text and images, creates submission, and executes the Tri-Engine pipeline.
    """
    filename = (file.filename or "").lower()
    allowed_exts = (".pdf", ".docx", ".doc", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp")
    if not filename.endswith(allowed_exts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Allowed: {allowed_exts}",
        )

    file_bytes = file.file.read()
    if len(file_bytes) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed threshold of 25MB",
        )

    extracted_text = ""
    extracted_images: List[bytes] = []

    if filename.endswith(".pdf"):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        parsed = parse_pdf(tmp_path, extract_images=True)
        extracted_text = parsed.full_text
        extracted_images = [img["raw_bytes"] for img in parsed.images if "raw_bytes" in img]
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    elif filename.endswith((".docx", ".doc")):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        parsed = parse_docx(tmp_path, extract_images=True)
        extracted_text = parsed.full_text
        extracted_images = [img["raw_bytes"] for img in parsed.images if "raw_bytes" in img]
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    elif filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
        extracted_images = [file_bytes]
        extracted_text = f"Visual Asset: {file.filename}"

    else:
        extracted_text = file_bytes.decode("utf-8", errors="ignore")

    # Create submission
    submission = Submission(
        organization_id=current_user.organization_id,
        creator_id=current_user.id,
        title=title,
        target_channel=target_channel,
        current_status=SubmissionStatus.DRAFT,
    )
    db.add(submission)
    db.flush()

    # Run Tri-Engine audit
    result = run_unified_audit_pipeline(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        submission_id=submission.id,
        content=extracted_text,
        image_bytes_list=extracted_images,
    )

    findings_stmt = (
        select(Finding)
        .options(selectinload(Finding.decision))
        .where(Finding.content_version_id == result.content_version_id)
        .order_by(Finding.created_at.asc())
    )
    fetched_findings = db.execute(findings_stmt).scalars().all()

    ver_stmt = select(ContentVersion).where(ContentVersion.id == result.content_version_id)
    version = db.execute(ver_stmt).scalar_one()

    return AuditRunResponse(
        submission_id=submission.id,
        version_id=version.id,
        version_number=version.version_number,
        audit_score=result.audit_score,
        findings=[FindingResponse.model_validate(f) for f in fetched_findings],
        summary=result.summary,
    )

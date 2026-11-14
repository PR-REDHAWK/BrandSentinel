import enum
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class SubmissionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    AUDITED = "AUDITED"
    IN_REVIEW = "IN_REVIEW"
    ESCALATED = "ESCALATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AuditEngine(str, enum.Enum):
    DETERMINISTIC = "DETERMINISTIC"
    RAG_LLM = "RAG_LLM"
    VISION_OCR = "VISION_OCR"


class FindingSeverity(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class DecisionAction(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"


class Submission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "submissions"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    creator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_channel: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, native_enum=False), default=SubmissionStatus.DRAFT, nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="submissions")
    creator: Mapped["User"] = relationship("User", back_populates="submissions")
    versions: Mapped[List["ContentVersion"]] = relationship(
        "ContentVersion", back_populates="submission", cascade="all, delete-orphan", order_by="ContentVersion.version_number"
    )


class ContentVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "content_versions"

    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    has_images: Mapped[bool] = mapped_column(Boolean, default=False)
    image_metadata: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    audit_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0 to 100

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="versions")
    findings: Mapped[List["Finding"]] = relationship(
        "Finding", back_populates="content_version", cascade="all, delete-orphan"
    )
    comments: Mapped[List["ReviewComment"]] = relationship(
        "ReviewComment", back_populates="content_version", cascade="all, delete-orphan"
    )


class Finding(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "findings"

    content_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_versions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    engine: Mapped[AuditEngine] = mapped_column(Enum(AuditEngine, native_enum=False), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity, native_enum=False), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detected_content: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source_citation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_passage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    content_version: Mapped["ContentVersion"] = relationship("ContentVersion", back_populates="findings")
    decision: Mapped[Optional["FindingDecision"]] = relationship(
        "FindingDecision", back_populates="finding", uselist=False, cascade="all, delete-orphan"
    )


class FindingDecision(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "finding_decisions"

    finding_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("findings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    decision: Mapped[DecisionAction] = mapped_column(Enum(DecisionAction, native_enum=False), nullable=False)
    custom_edit: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    finding: Mapped["Finding"] = relationship("Finding", back_populates="decision")
    user: Mapped["User"] = relationship("User", back_populates="decisions")


class ReviewComment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "review_comments"

    content_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_versions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    finding_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    content_version: Mapped["ContentVersion"] = relationship("ContentVersion", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")

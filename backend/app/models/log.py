from typing import Any, Dict, Optional
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    # e.g. LOGIN, GUIDELINE_UPLOAD, AUDIT_RUN, FINDING_DECIDED, CONTENT_APPROVED, OVERRIDE
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="audit_logs")

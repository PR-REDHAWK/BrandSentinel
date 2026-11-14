from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Guideline(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "guidelines"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PDF, DOCX, TXT
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")  # ACTIVE, ARCHIVED
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="guidelines")
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="guideline", cascade="all, delete-orphan"
    )


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_chunks"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    guideline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("guidelines.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Stored as serialized float array for universal compatibility across SQLite & Postgres
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    guideline: Mapped["Guideline"] = relationship("Guideline", back_populates="chunks")


class ApprovedFact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "approved_facts"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # Pricing, Performance, Metrics, Legal
    claim_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    approved_truth: Mapped[str] = mapped_column(Text, nullable=False)
    mandatory_caveat: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_citation: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_from: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expires_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="approved_facts")


class GlossaryTerm(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "glossary_terms"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    term: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_term: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    definition_or_rule: Mapped[str] = mapped_column(Text, nullable=False)
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="glossary_terms")


class BrandAsset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "brand_assets"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # LOGO, PALETTE, TYPOGRAPHY
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hex_colors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # e.g. ["#0B2046", "#FF6B35"]
    aspect_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rules: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="brand_assets")

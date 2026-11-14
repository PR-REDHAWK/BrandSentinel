import enum
from typing import List, Optional
from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    CREATOR = "CREATOR"
    BRAND_MANAGER = "BRAND_MANAGER"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    guidelines: Mapped[List["Guideline"]] = relationship(
        "Guideline", back_populates="organization", cascade="all, delete-orphan"
    )
    approved_facts: Mapped[List["ApprovedFact"]] = relationship(
        "ApprovedFact", back_populates="organization", cascade="all, delete-orphan"
    )
    glossary_terms: Mapped[List["GlossaryTerm"]] = relationship(
        "GlossaryTerm", back_populates="organization", cascade="all, delete-orphan"
    )
    brand_assets: Mapped[List["BrandAsset"]] = relationship(
        "BrandAsset", back_populates="organization", cascade="all, delete-orphan"
    )
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission", back_populates="organization", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="organization", cascade="all, delete-orphan"
    )


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), default=UserRole.CREATOR, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="creator")
    decisions: Mapped[List["FindingDecision"]] = relationship("FindingDecision", back_populates="user")
    comments: Mapped[List["ReviewComment"]] = relationship("ReviewComment", back_populates="user")

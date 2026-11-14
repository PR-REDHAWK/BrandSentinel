from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user, require_role
from app.models.auth import Organization, User, UserRole
from app.models.log import AuditLog

router = APIRouter(prefix="/admin", tags=["Organization Admin & User Management"])


# ==================== SCHEMAS ====================

class UserAdminView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: Any


class UpdateRoleRequest(BaseModel):
    role: UserRole = Field(..., description="Target role: CREATOR, REVIEWER, BRAND_MANAGER, ADMIN")


class UpdateStatusRequest(BaseModel):
    is_active: bool = Field(..., description="Active status for user access")


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str]
    event_type: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    created_at: Any


# ==================== ENDPOINTS ====================

@router.get("/organization")
def get_organization_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the current organization profile and high-level membership counts."""
    org = db.get(Organization, current_user.organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    user_count_stmt = select(func.count(User.id)).where(User.organization_id == org.id)
    total_users = db.execute(user_count_stmt).scalar() or 0

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "total_members": total_users,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


@router.get("/users", response_model=List[UserAdminView])
def list_organization_users(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.BRAND_MANAGER])),
    db: Session = Depends(get_db),
):
    """List all users within the current user's organization."""
    stmt = (
        select(User)
        .where(User.organization_id == current_user.organization_id)
        .order_by(User.created_at.desc())
    )
    users = db.execute(stmt).scalars().all()
    return [UserAdminView.model_validate(u) for u in users]


@router.patch("/users/{user_id}/role", response_model=UserAdminView)
def update_user_role(
    user_id: str,
    payload: UpdateRoleRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Assign or modify a user's role within the organization. Admin only."""
    user = db.get(User, user_id)
    if not user or user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Prevent admin from demoting themselves if they are the only admin
    if user.id == current_user.id and payload.role != UserRole.ADMIN:
        admin_count_stmt = select(func.count(User.id)).where(
            User.organization_id == current_user.organization_id,
            User.role == UserRole.ADMIN,
            User.is_active == True,
        )
        admin_count = db.execute(admin_count_stmt).scalar() or 0
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the sole active administrator in the organization.",
            )

    old_role = user.role
    user.role = payload.role

    # Record Audit Log
    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type="USER_ROLE_CHANGED",
        entity_type="User",
        entity_id=user.id,
        details={
            "user_email": user.email,
            "old_role": old_role.value if hasattr(old_role, "value") else str(old_role),
            "new_role": payload.role.value,
        },
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return UserAdminView.model_validate(user)


@router.patch("/users/{user_id}/status", response_model=UserAdminView)
def update_user_status(
    user_id: str,
    payload: UpdateStatusRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a user account. Admin only."""
    user = db.get(User, user_id)
    if not user or user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own administrator account.",
        )

    user.is_active = payload.is_active

    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type="USER_STATUS_CHANGED",
        entity_type="User",
        entity_id=user.id,
        details={
            "user_email": user.email,
            "is_active": payload.is_active,
        },
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return UserAdminView.model_validate(user)


@router.get("/audit-logs", response_model=List[AuditLogEntry])
def list_audit_trail(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = Query(None, description="Optional filter by event_type"),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.BRAND_MANAGER])),
    db: Session = Depends(get_db),
):
    """Query organization audit trail logs with timestamps, event types, and responsible actors."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.organization_id == current_user.organization_id)
    )
    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)

    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    logs = db.execute(stmt).scalars().all()
    return [AuditLogEntry.model_validate(l) for l in logs]

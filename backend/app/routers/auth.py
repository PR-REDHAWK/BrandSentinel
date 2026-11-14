import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.auth import Organization, User, UserRole
from app.models.log import AuditLog
from app.schemas.auth import (
    OrganizationResponse,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s or "org"


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user and either create their organization or join an existing one.
    """
    existing_user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    org_slug = payload.organization_slug or slugify(payload.organization_name)
    org = db.execute(select(Organization).where(Organization.slug == org_slug)).scalar_one_or_none()

    if not org:
        org = Organization(name=payload.organization_name, slug=org_slug)
        db.add(org)
        db.flush()
        assigned_role = payload.role if payload.role == UserRole.ADMIN else UserRole.ADMIN
    else:
        assigned_role = payload.role

    new_user = User(
        organization_id=org.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=assigned_role,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    audit_log = AuditLog(
        organization_id=org.id,
        user_id=new_user.id,
        event_type="USER_REGISTERED",
        entity_type="User",
        entity_id=new_user.id,
        details={"email": new_user.email, "role": new_user.role.value},
    )
    db.add(audit_log)
    db.commit()

    stmt = select(User).options(selectinload(User.organization)).where(User.id == new_user.id)
    user_with_org = db.execute(stmt).scalar_one()

    token_data = {
        "sub": user_with_org.id,
        "org_id": user_with_org.organization_id,
        "role": user_with_org.role.value,
    }
    access_token = create_access_token(data=token_data)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user_with_org),
    )


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive a JWT token."""
    stmt = select(User).options(selectinload(User.organization)).where(User.email == payload.email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    audit_log = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="USER_LOGIN",
        entity_type="User",
        entity_id=user.id,
        details={"email": user.email},
    )
    db.add(audit_log)
    db.commit()

    token_data = {
        "sub": user.id,
        "org_id": user.organization_id,
        "role": user.role.value,
    }
    access_token = create_access_token(data=token_data)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Retrieve currently authenticated user profile and organization details."""
    return UserResponse.model_validate(current_user)

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.auth import UserRole
from app.routers.auth import get_current_user_profile, login, register
from app.schemas.auth import UserLogin, UserRegister


def test_register_and_login_flow(db: Session):
    # 1. Register User
    reg_payload = UserRegister(
        email="sarah@acme.com",
        password="StrongPassword123!",
        full_name="Sarah Connor",
        role=UserRole.ADMIN,
        organization_name="Acme Corporation",
    )
    token_resp = register(payload=reg_payload, db=db)
    assert token_resp.access_token is not None
    assert token_resp.user.email == "sarah@acme.com"
    assert token_resp.user.role == UserRole.ADMIN

    # 2. Login
    login_payload = UserLogin(email="sarah@acme.com", password="StrongPassword123!")
    login_resp = login(payload=login_payload, db=db)
    assert login_resp.access_token is not None

    # 3. Invalid Login
    with pytest.raises(HTTPException) as exc:
        login(payload=UserLogin(email="sarah@acme.com", password="BadPassword!"), db=db)
    assert exc.value.status_code == 401


def test_duplicate_registration_prevented(db: Session):
    reg_payload = UserRegister(
        email="duplicate@acme.com",
        password="Password123!",
        full_name="User One",
        role=UserRole.CREATOR,
        organization_name="Acme Corp",
    )
    register(payload=reg_payload, db=db)

    with pytest.raises(HTTPException) as exc:
        register(payload=reg_payload, db=db)
    assert exc.value.status_code == 400

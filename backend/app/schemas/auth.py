from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.auth import UserRole


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=2, max_length=100)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    created_at: datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = Field(default=UserRole.CREATOR)
    organization_name: str = Field(..., min_length=2, max_length=255)
    organization_slug: Optional[str] = Field(None, min_length=2, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    organization: Optional[OrganizationResponse] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str
    settings_json: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class OrganizationMemberOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    org_id: uuid.UUID
    role: str
    user: UserOut | None = None

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    org_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    user: UserOut
    orgs: list[OrganizationOut]
    current_org: OrganizationOut | None = None
    role: str | None = None


class UpdateOrgRequest(BaseModel):
    name: str | None = None
    settings_json: dict | None = None


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "viewer"


class UpdateMemberRoleRequest(BaseModel):
    role: str


class Meta(BaseModel):
    page: int = 1
    per_page: int = 20
    total: int = 0


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)

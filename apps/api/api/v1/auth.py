import re
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import log_audit
from core.security import (
    create_access_token,
    create_refresh_token_value,
    hash_password,
    hash_token,
    refresh_token_expiry,
    verify_password,
)
from database import get_db
from dependencies import AuthContext, get_auth_context
from models.user import Organization, OrganizationMember, RefreshToken, User
from schemas.auth import (
    AuthMeResponse,
    LoginRequest,
    OrganizationMemberOut,
    OrganizationOut,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdateMemberRoleRequest,
    UpdateOrgRequest,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "org"


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=body.email, password_hash=hash_password(body.password), name=body.name)
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc

    base_slug = slugify(body.org_name)
    slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

    org = Organization(name=body.org_name, slug=slug)
    db.add(org)
    await db.flush()

    membership = OrganizationMember(org_id=org.id, user_id=user.id, role="admin")
    db.add(membership)

    refresh_value = create_refresh_token_value()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_value),
            expires_at=refresh_token_expiry(),
        )
    )

    access = create_access_token(user.id, org.id)
    return TokenResponse(access_token=access, refresh_token=refresh_value)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    membership_result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id).limit(1)
    )
    membership = membership_result.scalar_one_or_none()
    org_id = membership.org_id if membership else None

    refresh_value = create_refresh_token_value()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_value),
            expires_at=refresh_token_expiry(),
        )
    )

    access = create_access_token(user.id, org_id)
    return TokenResponse(access_token=access, refresh_token=refresh_value)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    stored.revoked = True

    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    membership_result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id).limit(1)
    )
    membership = membership_result.scalar_one_or_none()

    new_refresh = create_refresh_token_value()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_refresh),
            expires_at=refresh_token_expiry(),
        )
    )

    access = create_access_token(user.id, membership.org_id if membership else None)
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked = True
    return {"ok": True}


@router.get("/me", response_model=AuthMeResponse)
async def me(
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    memberships = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization, Organization.id == OrganizationMember.org_id)
        .where(OrganizationMember.user_id == ctx.user.id)
    )
    orgs = [org for _, org in memberships.all()]
    current = next((o for o in orgs if o.id == ctx.org_id), orgs[0] if orgs else None)
    return AuthMeResponse(
        user=UserOut.model_validate(ctx.user),
        orgs=[OrganizationOut.model_validate(o) for o in orgs],
        current_org=OrganizationOut.model_validate(current) if current else None,
        role=ctx.role,
    )

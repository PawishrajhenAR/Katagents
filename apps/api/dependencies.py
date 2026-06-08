import uuid
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.rbac import has_min_role
from core.security import decode_access_token
from database import get_db
from models.user import OrganizationMember, User


@dataclass
class AuthContext:
    user: User
    org_id: uuid.UUID
    role: str


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_auth_context(
    user: User = Depends(get_current_user),
    x_org_id: str | None = Header(default=None, alias="X-Org-Id"),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    if not x_org_id:
        result = await db.execute(
            select(OrganizationMember).where(OrganizationMember.user_id == user.id).limit(1)
        )
        membership = result.scalar_one_or_none()
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No organization membership")
        return AuthContext(user=user, org_id=membership.org_id, role=membership.role)

    try:
        org_id = uuid.UUID(x_org_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid org id") from e

    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.org_id == org_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")
    return AuthContext(user=user, org_id=org_id, role=membership.role)


def require_role(min_role: str):
    async def checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not has_min_role(ctx.role, min_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return ctx

    return checker

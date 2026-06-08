import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import log_audit
from core.rbac import can_manage_org
from database import get_db
from dependencies import AuthContext, get_auth_context, require_role
from models.user import Organization, OrganizationMember, OrgRole, User
from schemas.auth import (
    InviteMemberRequest,
    OrganizationMemberOut,
    OrganizationOut,
    UpdateMemberRoleRequest,
    UpdateOrgRequest,
    UserOut,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/current", response_model=OrganizationOut)
async def get_current_org(ctx: AuthContext = Depends(get_auth_context), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization).where(Organization.id == ctx.org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return OrganizationOut.model_validate(org)


@router.patch("/current", response_model=OrganizationOut)
async def update_current_org(
    body: UpdateOrgRequest,
    ctx: AuthContext = Depends(require_role(OrgRole.ADMIN.value)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.id == ctx.org_id))
    org = result.scalar_one()
    if body.name is not None:
        org.name = body.name
    if body.settings_json is not None:
        org.settings_json = body.settings_json
    await log_audit(
        db, org_id=ctx.org_id, user_id=ctx.user.id, action="org.update",
        resource_type="organization", resource_id=str(org.id),
    )
    return OrganizationOut.model_validate(org)


@router.get("/members", response_model=list[OrganizationMemberOut])
async def list_members(ctx: AuthContext = Depends(get_auth_context), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.org_id == ctx.org_id)
    )
    members = []
    for membership, user in result.all():
        out = OrganizationMemberOut.model_validate(membership)
        out.user = UserOut.model_validate(user)
        members.append(out)
    return members


@router.patch("/members/{member_id}", response_model=OrganizationMemberOut)
async def update_member_role(
    member_id: uuid.UUID,
    body: UpdateMemberRoleRequest,
    ctx: AuthContext = Depends(require_role(OrgRole.ADMIN.value)),
    db: AsyncSession = Depends(get_db),
):
    if body.role not in [r.value for r in OrgRole]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.org_id == ctx.org_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    membership.role = body.role
    return OrganizationMemberOut.model_validate(membership)

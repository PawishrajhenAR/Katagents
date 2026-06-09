import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import log_audit
from core.rbac import can_write_campaigns
from database import get_db
from dependencies import AuthContext, get_auth_context, require_role
from models.campaign import Campaign, CampaignLead, CampaignStatus
from models.email import EmailDraft
from models.user import OrgRole
from schemas.campaign import CampaignCreate, CampaignOut, CampaignUpdate

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


async def _campaign_stats(db: AsyncSession, campaign_id: uuid.UUID) -> tuple[int, int]:
    stats = await _batch_campaign_stats(db, [campaign_id])
    return stats.get(campaign_id, (0, 0))


async def _batch_campaign_stats(
    db: AsyncSession, campaign_ids: list[uuid.UUID]
) -> dict[uuid.UUID, tuple[int, int]]:
    if not campaign_ids:
        return {}

    lead_result = await db.execute(
        select(CampaignLead.campaign_id, func.count())
        .where(CampaignLead.campaign_id.in_(campaign_ids))
        .group_by(CampaignLead.campaign_id)
    )
    pending_result = await db.execute(
        select(EmailDraft.campaign_id, func.count())
        .where(
            EmailDraft.campaign_id.in_(campaign_ids),
            EmailDraft.status == "pending",
        )
        .group_by(EmailDraft.campaign_id)
    )

    lead_counts = {row[0]: row[1] for row in lead_result.all()}
    pending_counts = {row[0]: row[1] for row in pending_result.all()}
    return {
        cid: (lead_counts.get(cid, 0), pending_counts.get(cid, 0))
        for cid in campaign_ids
    }


def _to_out(campaign: Campaign, lead_count: int, pending: int) -> CampaignOut:
    return CampaignOut(
        id=campaign.id,
        org_id=campaign.org_id,
        name=campaign.name,
        agent_type=campaign.agent_type,
        status=campaign.status,
        config_json=campaign.config_json or {},
        created_by=campaign.created_by,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        lead_count=lead_count,
        pending_drafts=pending,
    )


@router.get("", response_model=dict)
async def list_campaigns(
    agent_type: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    query = select(Campaign).where(
        Campaign.org_id == ctx.org_id,
        Campaign.deleted_at.is_(None),
    )
    if agent_type:
        query = query.where(Campaign.agent_type == agent_type)
    if status_filter:
        query = query.where(Campaign.status == status_filter)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query.order_by(Campaign.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    campaigns = result.scalars().all()
    stats = await _batch_campaign_stats(db, [c.id for c in campaigns])
    data = [_to_out(c, *stats.get(c.id, (0, 0))) for c in campaigns]
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total or 0}}


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    campaign = Campaign(
        org_id=ctx.org_id,
        name=body.name,
        agent_type=body.agent_type,
        config_json=body.config_json,
        created_by=ctx.user.id,
        status=CampaignStatus.DRAFT.value,
    )
    db.add(campaign)
    await db.flush()
    await log_audit(
        db, org_id=ctx.org_id, user_id=ctx.user.id, action="campaign.create",
        resource_type="campaign", resource_id=str(campaign.id),
    )
    return _to_out(campaign, 0, 0)


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: uuid.UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.org_id == ctx.org_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    lc, pd = await _campaign_stats(db, campaign.id)
    return _to_out(campaign, lc, pd)


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: uuid.UUID,
    body: CampaignUpdate,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == ctx.org_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if body.name is not None:
        campaign.name = body.name
    if body.status is not None:
        campaign.status = body.status
    if body.config_json is not None:
        campaign.config_json = body.config_json
    lc, pd = await _campaign_stats(db, campaign.id)
    return _to_out(campaign, lc, pd)


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: uuid.UUID,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    from datetime import UTC, datetime

    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == ctx.org_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    campaign.deleted_at = datetime.now(UTC)
    campaign.status = CampaignStatus.ARCHIVED.value
    return {"ok": True}

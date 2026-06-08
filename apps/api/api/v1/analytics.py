import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import AuthContext, get_auth_context
from models.campaign import Campaign, CampaignLead, LeadStatus
from models.email import Email, EmailDraft, EmailReply
from schemas.analytics import AnalyticsOverview, CampaignAnalytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    total_campaigns = await db.scalar(
        select(func.count()).select_from(Campaign).where(
            Campaign.org_id == ctx.org_id, Campaign.deleted_at.is_(None)
        )
    )
    active_campaigns = await db.scalar(
        select(func.count()).select_from(Campaign).where(
            Campaign.org_id == ctx.org_id,
            Campaign.status == "active",
            Campaign.deleted_at.is_(None),
        )
    )
    total_leads = await db.scalar(
        select(func.count()).select_from(CampaignLead)
        .join(Campaign, Campaign.id == CampaignLead.campaign_id)
        .where(Campaign.org_id == ctx.org_id)
    )
    emails_sent = await db.scalar(
        select(func.count()).select_from(Email).where(
            Email.org_id == ctx.org_id, Email.status.in_(["sent", "delivered"])
        )
    )
    emails_delivered = await db.scalar(
        select(func.count()).select_from(Email).where(
            Email.org_id == ctx.org_id, Email.status == "delivered"
        )
    )
    replies = await db.scalar(
        select(func.count()).select_from(EmailReply)
        .join(Email, Email.id == EmailReply.email_id)
        .where(Email.org_id == ctx.org_id)
    )
    pending = await db.scalar(
        select(func.count()).select_from(EmailDraft)
        .join(Campaign, Campaign.id == EmailDraft.campaign_id)
        .where(Campaign.org_id == ctx.org_id, EmailDraft.status == "pending")
    )
    sent = emails_sent or 0
    reply_count = replies or 0
    return AnalyticsOverview(
        total_campaigns=total_campaigns or 0,
        active_campaigns=active_campaigns or 0,
        total_leads=total_leads or 0,
        emails_sent=sent,
        emails_delivered=emails_delivered or 0,
        replies_received=reply_count,
        reply_rate=round(reply_count / sent * 100, 2) if sent else 0.0,
        pending_approvals=pending or 0,
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignAnalytics)
async def campaign_analytics(
    campaign_id: uuid.UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    campaign = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == ctx.org_id)
    )
    if not campaign.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    leads_total = await db.scalar(
        select(func.count()).select_from(CampaignLead).where(CampaignLead.campaign_id == campaign_id)
    )
    researched = await db.scalar(
        select(func.count()).select_from(CampaignLead).where(
            CampaignLead.campaign_id == campaign_id,
            CampaignLead.status.in_([LeadStatus.RESEARCHED.value, LeadStatus.DRAFT_PENDING.value,
                                     LeadStatus.APPROVED.value, LeadStatus.SENT.value, LeadStatus.REPLIED.value]),
        )
    )
    drafts_pending = await db.scalar(
        select(func.count()).select_from(EmailDraft).where(
            EmailDraft.campaign_id == campaign_id, EmailDraft.status == "pending"
        )
    )
    drafts_approved = await db.scalar(
        select(func.count()).select_from(EmailDraft).where(
            EmailDraft.campaign_id == campaign_id, EmailDraft.status == "approved"
        )
    )
    emails_sent = await db.scalar(
        select(func.count()).select_from(Email).where(Email.campaign_id == campaign_id)
    )
    reply_count = await db.scalar(
        select(func.count()).select_from(EmailReply)
        .join(Email, Email.id == EmailReply.email_id)
        .where(Email.campaign_id == campaign_id)
    )

    classification_result = await db.execute(
        select(EmailReply.classification, func.count())
        .join(Email, Email.id == EmailReply.email_id)
        .where(Email.campaign_id == campaign_id, EmailReply.classification.isnot(None))
        .group_by(EmailReply.classification)
    )
    classifications = {row[0]: row[1] for row in classification_result.all()}

    return CampaignAnalytics(
        campaign_id=str(campaign_id),
        leads_total=leads_total or 0,
        researched=researched or 0,
        drafts_pending=drafts_pending or 0,
        drafts_approved=drafts_approved or 0,
        emails_sent=emails_sent or 0,
        replies=reply_count or 0,
        classifications=classifications,
    )

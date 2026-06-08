import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import AuthContext, get_auth_context, require_role
from models.campaign import Campaign
from models.email import Email, EmailReply
from models.user import OrgRole
from schemas.email import EmailOut, ReplyClassificationUpdate, ReplyOut

router = APIRouter(tags=["emails"])


@router.get("/campaigns/{campaign_id}/emails", response_model=dict)
async def list_emails(
    campaign_id: uuid.UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Email, Campaign)
        .join(Campaign, Campaign.id == Email.campaign_id)
        .where(Email.campaign_id == campaign_id, Campaign.org_id == ctx.org_id)
        .order_by(Email.created_at.desc())
    )
    emails = [EmailOut.model_validate(e) for e, _ in result.all()]
    return {"data": emails}


@router.get("/campaigns/{campaign_id}/replies", response_model=dict)
async def list_replies(
    campaign_id: uuid.UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailReply, Email, Campaign)
        .join(Email, Email.id == EmailReply.email_id)
        .join(Campaign, Campaign.id == Email.campaign_id)
        .where(Email.campaign_id == campaign_id, Campaign.org_id == ctx.org_id)
        .order_by(EmailReply.received_at.desc())
    )
    replies = [ReplyOut.model_validate(r) for r, _, _ in result.all()]
    return {"data": replies}


@router.patch("/replies/{reply_id}", response_model=ReplyOut)
async def update_reply_classification(
    reply_id: uuid.UUID,
    body: ReplyClassificationUpdate,
    ctx: AuthContext = Depends(require_role(OrgRole.REVIEWER.value)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailReply, Email, Campaign)
        .join(Email, Email.id == EmailReply.email_id)
        .join(Campaign, Campaign.id == Email.campaign_id)
        .where(EmailReply.id == reply_id, Campaign.org_id == ctx.org_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found")
    reply, _, _ = row
    reply.classification = body.classification
    return ReplyOut.model_validate(reply)

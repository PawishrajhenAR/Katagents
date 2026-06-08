from sqlalchemy import select

from agents.base import AgentContext, StepResult
from models.campaign import CampaignLead, Lead, LeadStatus
from models.email import EmailDraft


async def run_sender(ctx: AgentContext) -> StepResult:
    from core.rate_limit import RateLimitService, get_redis

    redis = await get_redis()
    rate_limiter = RateLimitService(redis)
    if not await rate_limiter.check_org_email_limit(str(ctx.org_id)):
        return StepResult(success=False, error="Daily email send limit reached for organization")

    result = await ctx.db.execute(
        select(EmailDraft, Lead)
        .join(Lead, Lead.id == EmailDraft.lead_id)
        .where(
            EmailDraft.campaign_id == ctx.campaign_id,
            EmailDraft.agent_run_id == ctx.run_id,
            EmailDraft.status == "approved",
        )
    )
    rows = result.all()
    sent = 0

    for draft, lead in rows:
        await ctx.services.email.send_email(
            to_email=lead.email,
            subject=draft.subject,
            body=draft.body,
            campaign_id=ctx.campaign_id,
            lead_id=lead.id,
            org_id=ctx.org_id,
            draft_id=draft.id,
        )
        draft.status = "sent"

        cl_result = await ctx.db.execute(
            select(CampaignLead).where(
                CampaignLead.campaign_id == ctx.campaign_id,
                CampaignLead.lead_id == lead.id,
            )
        )
        cl = cl_result.scalar_one_or_none()
        if cl:
            cl.status = LeadStatus.SENT.value
        lead.status = LeadStatus.SENT.value
        sent += 1

        await ctx.services.analytics.track(
            org_id=ctx.org_id,
            event_name="email.sent",
            campaign_id=ctx.campaign_id,
            run_id=ctx.run_id,
            properties={"lead_id": str(lead.id)},
        )

    ctx.log("info", f"Sent {sent} emails")
    return StepResult(success=True, output={"emails_sent": sent})

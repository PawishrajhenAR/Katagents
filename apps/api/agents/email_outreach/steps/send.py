from sqlalchemy import select, update

from agents.base import AgentContext, StepResult
from models.campaign import CampaignLead, Lead, LeadStatus
from models.email import EmailDraft, EmailStatus


async def run_sender(ctx: AgentContext) -> StepResult:
    from core.rate_limit import check_org_email_limit

    if not await check_org_email_limit(str(ctx.org_id)):
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
    failed = 0
    errors: list[str] = []

    for draft, lead in rows:
        email_record = await ctx.services.email.send_email(
            to_email=lead.email,
            subject=draft.subject,
            body=draft.body,
            campaign_id=ctx.campaign_id,
            lead_id=lead.id,
            org_id=ctx.org_id,
            draft_id=draft.id,
        )
        if email_record.status != EmailStatus.SENT.value:
            failed += 1
            errors.append(f"{lead.email}: delivery failed (check Resend limits or use pawishgpt@gmail.com for testing)")
            continue

        draft.status = "sent"
        await ctx.db.execute(
            update(CampaignLead)
            .where(
                CampaignLead.campaign_id == ctx.campaign_id,
                CampaignLead.lead_id == lead.id,
            )
            .values(status=LeadStatus.SENT.value)
        )
        await ctx.db.execute(
            update(Lead).where(Lead.id == lead.id).values(status=LeadStatus.SENT.value)
        )
        sent += 1

        await ctx.services.analytics.track(
            org_id=ctx.org_id,
            event_name="email.sent",
            campaign_id=ctx.campaign_id,
            run_id=ctx.run_id,
            properties={"lead_id": str(lead.id)},
        )

    ctx.log("info", f"Sent {sent} emails" + (f", {failed} failed" if failed else ""))

    if sent == 0 and failed > 0:
        return StepResult(success=False, error="; ".join(errors[:3]))

    return StepResult(
        success=True,
        output={"emails_sent": sent, "emails_failed": failed, "errors": errors},
    )

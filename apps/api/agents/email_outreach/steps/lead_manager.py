import re

from sqlalchemy import select

from agents.base import AgentContext, StepResult
from models.campaign import CampaignLead, Lead, LeadStatus
from models.email import Unsubscribe


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


async def run_lead_manager(ctx: AgentContext) -> StepResult:
    unsub_result = await ctx.db.execute(
        select(Unsubscribe.email).where(Unsubscribe.org_id == ctx.org_id)
    )
    unsubscribed = set(unsub_result.scalars().all())

    result = await ctx.db.execute(
        select(CampaignLead, Lead)
        .join(Lead, Lead.id == CampaignLead.lead_id)
        .where(CampaignLead.campaign_id == ctx.campaign_id)
    )

    ready = 0
    skipped = 0

    for cl, lead in result.all():
        if cl.status == LeadStatus.SKIPPED.value:
            skipped += 1
            continue

        if lead.email in unsubscribed or not _valid_email(lead.email):
            cl.status = LeadStatus.SKIPPED.value
            skipped += 1
            continue

        cl.status = LeadStatus.READY.value
        lead.status = LeadStatus.READY.value
        ready += 1

    ctx.log("info", f"Lead manager: {ready} ready, {skipped} skipped")
    return StepResult(success=True, output={"ready_leads": ready, "skipped_leads": skipped})

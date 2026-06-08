import re

from sqlalchemy import select

from agents.base import AgentContext, StepResult
from models.campaign import CampaignLead, Lead, LeadStatus
from models.email import Unsubscribe


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


async def run_lead_manager(ctx: AgentContext) -> StepResult:
    result = await ctx.db.execute(
        select(CampaignLead).where(CampaignLead.campaign_id == ctx.campaign_id)
    )
    campaign_leads = result.scalars().all()

    ready = 0
    skipped = 0

    for cl in campaign_leads:
        lead_result = await ctx.db.execute(select(Lead).where(Lead.id == cl.lead_id))
        lead = lead_result.scalar_one()

        unsub = await ctx.db.execute(
            select(Unsubscribe).where(Unsubscribe.org_id == ctx.org_id, Unsubscribe.email == lead.email)
        )
        if unsub.scalar_one_or_none() or not _valid_email(lead.email):
            cl.status = LeadStatus.SKIPPED.value
            skipped += 1
            continue

        cl.status = LeadStatus.READY.value
        lead.status = LeadStatus.READY.value
        ready += 1

    ctx.log("info", f"Lead manager: {ready} ready, {skipped} skipped")
    return StepResult(success=True, output={"ready_leads": ready, "skipped_leads": skipped})

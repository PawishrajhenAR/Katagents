from sqlalchemy import select

from agents.base import AgentContext, StepResult
from models.campaign import CampaignLead, Lead, LeadStatus


async def run_research(ctx: AgentContext) -> StepResult:
    result = await ctx.db.execute(
        select(CampaignLead, Lead)
        .join(Lead, Lead.id == CampaignLead.lead_id)
        .where(
            CampaignLead.campaign_id == ctx.campaign_id,
            CampaignLead.status.in_([LeadStatus.READY.value, LeadStatus.IMPORTED.value]),
        )
    )
    rows = result.all()
    researched = 0

    for cl, lead in rows:
        await ctx.services.research.research_lead(
            ctx.db,
            lead=lead,
            campaign_id=ctx.campaign_id,
            agent_run_id=ctx.run_id,
            org_settings=ctx.services.org_settings,
        )
        cl.status = LeadStatus.RESEARCHED.value
        lead.status = LeadStatus.RESEARCHED.value
        researched += 1

    ctx.log("info", f"Researched {researched} leads")
    return StepResult(success=True, output={"researched": researched})

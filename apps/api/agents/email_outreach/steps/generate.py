from sqlalchemy import select

from agents.base import AgentContext, StepResult
from models.campaign import CampaignLead, Lead, LeadStatus
from models.email import EmailDraft, ResearchRecord


GENERATE_SYSTEM = (
    "You are an expert B2B email copywriter. Return valid JSON only with keys: "
    "subject (string, max 80 chars), body (string, plain text, under 200 words). "
    "Never use aggressive or spammy language. Include a clear but soft call to action."
)


async def run_email_generator(ctx: AgentContext) -> StepResult:
    tone = ctx.config.get("tone", ctx.services.org_settings.get("tone", "professional"))
    banned = ctx.services.org_settings.get("banned_phrases", [])

    result = await ctx.db.execute(
        select(CampaignLead, Lead)
        .join(Lead, Lead.id == CampaignLead.lead_id)
        .where(
            CampaignLead.campaign_id == ctx.campaign_id,
            CampaignLead.status == LeadStatus.RESEARCHED.value,
        )
    )
    rows = result.all()
    generated = 0

    for cl, lead in rows:
        research_result = await ctx.db.execute(
            select(ResearchRecord)
            .where(ResearchRecord.lead_id == lead.id, ResearchRecord.campaign_id == ctx.campaign_id)
            .order_by(ResearchRecord.created_at.desc())
            .limit(1)
        )
        research = research_result.scalar_one_or_none()
        summary = research.summary if research else "No research available."

        prompt = f"""Write a personalized cold outreach email.
Prospect: {lead.first_name or 'there'} {lead.last_name or ''} at {lead.company or 'their company'}
Title: {lead.title or 'Unknown'}
Research: {summary}
Tone: {tone}
Banned phrases: {', '.join(banned) if banned else 'none'}

Return JSON with subject and body."""

        email_content = await ctx.services.llm.generate_json(prompt, GENERATE_SYSTEM)
        subject = str(email_content.get("subject", "Following up"))[:500]
        body = str(email_content.get("body", ""))

        for phrase in banned:
            if phrase.lower() in body.lower():
                body = body.replace(phrase, "")

        draft = EmailDraft(
            campaign_id=ctx.campaign_id,
            lead_id=lead.id,
            agent_run_id=ctx.run_id,
            subject=subject,
            body=body,
            status="pending",
        )
        ctx.db.add(draft)
        await ctx.db.flush()
        await ctx.services.approval.create_approval_item(draft)

        cl.status = LeadStatus.DRAFT_PENDING.value
        lead.status = LeadStatus.DRAFT_PENDING.value
        generated += 1

    ctx.log("info", f"Generated {generated} email drafts")
    return StepResult(success=True, output={"drafts_generated": generated})

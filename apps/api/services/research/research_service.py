import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.campaign import Lead
from models.email import ResearchRecord
from services.llm.provider import LLMService


class ResearchService:
    RESEARCH_SYSTEM = (
        "You are a B2B sales research assistant. Return valid JSON only with keys: "
        "summary (string), talking_points (array of strings), confidence (float 0-1)."
    )

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def research_lead(
        self,
        db: AsyncSession,
        *,
        lead: Lead,
        campaign_id: uuid.UUID,
        agent_run_id: uuid.UUID | None,
        org_settings: dict,
    ) -> ResearchRecord:
        icp = org_settings.get("icp", "B2B SaaS companies")
        tone = org_settings.get("tone", "professional and concise")

        prompt = f"""Research this prospect for outreach:
- Name: {lead.first_name or ''} {lead.last_name or ''}
- Email: {lead.email}
- Company: {lead.company or 'Unknown'}
- Title: {lead.title or 'Unknown'}
- ICP: {icp}
- Tone: {tone}

Provide a brief research summary and 3 talking points for personalized email outreach."""

        result = await self.llm.generate_json(prompt, self.RESEARCH_SYSTEM)
        record = ResearchRecord(
            lead_id=lead.id,
            campaign_id=campaign_id,
            agent_run_id=agent_run_id,
            summary=result.get("summary", str(result)),
            sources_json={"talking_points": result.get("talking_points", []), "raw": result},
            confidence=float(result.get("confidence", 0.5)),
        )
        db.add(record)
        await db.flush()
        return record

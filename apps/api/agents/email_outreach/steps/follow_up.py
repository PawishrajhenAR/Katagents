import json

from sqlalchemy import select

from agents.base import AgentContext, StepResult
from models.email import EmailReply


CLASSIFY_SYSTEM = (
    "Classify this email reply. Return JSON with keys: classification (one of: "
    "interested, objection, not_now, unsubscribe, ooo, other), confidence (0-1), reason (string)."
)


async def classify_reply_by_id(db, reply_id: str) -> None:
    import uuid

    from services.llm.provider import LLMService
    from services.shared import SharedServices

    result = await db.execute(select(EmailReply).where(EmailReply.id == uuid.UUID(reply_id)))
    reply = result.scalar_one_or_none()
    if not reply or reply.classification:
        return

    llm = LLMService()
    prompt = f"Classify this email reply:\n\nFrom: {reply.from_address}\n\n{reply.body_text[:3000]}"
    classification = await llm.generate_json(prompt, CLASSIFY_SYSTEM)
    reply.classification = classification.get("classification", "other")
    reply.classification_json = classification
    await db.commit()


async def run_follow_up_scheduler(ctx: AgentContext) -> StepResult:
    delay_days = ctx.config.get("follow_up_delay_days", 7)
    max_follow_ups = ctx.config.get("max_follow_ups", 2)

    ctx.log("info", f"Follow-up scheduler configured: {delay_days} days, max {max_follow_ups}")

    scheduled = await ctx.services.scheduler.enqueue_delayed(
        "schedule_follow_up",
        str(ctx.run_id),
        delay_days * 86400,
        campaign_id=str(ctx.campaign_id),
        org_id=str(ctx.org_id),
    )

    if not scheduled:
        ctx.log(
            "warning",
            "Follow-up job not queued — start Redis (docker compose up redis) for delayed follow-ups",
        )

    return StepResult(
        success=True,
        output={"follow_up_scheduled_days": delay_days, "follow_up_queued": scheduled},
    )

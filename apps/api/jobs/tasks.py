import uuid

from agents.email_outreach.steps.follow_up import classify_reply_by_id
from agents.engine import AgentExecutionEngine
from config import settings
from database import async_session_factory
from services.scheduler.scheduler_service import parse_redis_settings


async def execute_agent_run(ctx, run_id: str) -> None:
    async with async_session_factory() as db:
        engine = AgentExecutionEngine(db)
        await engine.execute_run(uuid.UUID(run_id))


async def classify_reply(ctx, reply_id: str) -> None:
    async with async_session_factory() as db:
        await classify_reply_by_id(db, reply_id)


async def schedule_follow_up(ctx, run_id: str, campaign_id: str, org_id: str) -> None:
    async with async_session_factory() as db:
        from sqlalchemy import select
        from models.campaign import CampaignLead, LeadStatus

        result = await db.execute(
            select(CampaignLead).where(
                CampaignLead.campaign_id == uuid.UUID(campaign_id),
                CampaignLead.status.in_([LeadStatus.SENT.value, LeadStatus.REPLIED.value]),
            )
        )
        leads = result.scalars().all()
        for cl in leads:
            if cl.status == LeadStatus.SENT.value:
                cl.status = LeadStatus.FOLLOW_UP_SCHEDULED.value
        await db.commit()


async def enqueue_agent_run(run_id: str) -> None:
    try:
        from services.scheduler.scheduler_service import get_arq_pool

        pool = await get_arq_pool()
        await pool.enqueue_job("execute_agent_run", run_id)
    except Exception:
        import uuid

        from agents.engine import AgentExecutionEngine
        from database import async_session_factory

        async with async_session_factory() as db:
            engine = AgentExecutionEngine(db)
            await engine.execute_run(uuid.UUID(run_id))


class WorkerSettings:
    functions = [execute_agent_run, classify_reply, schedule_follow_up]
    redis_settings = parse_redis_settings()
    max_jobs = 10
    job_timeout = 600

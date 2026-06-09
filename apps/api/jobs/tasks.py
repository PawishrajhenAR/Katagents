import asyncio
import logging
import uuid

from agents.email_outreach.steps.follow_up import classify_reply_by_id
from agents.engine import AgentExecutionEngine
from core.redis import mark_redis_unavailable, redis_is_available
from database import async_session_factory

from services.scheduler.scheduler_service import parse_redis_settings

logger = logging.getLogger(__name__)


async def execute_agent_run(ctx, run_id: str) -> None:
    async with async_session_factory() as db:
        try:
            engine = AgentExecutionEngine(db)
            await engine.execute_run(uuid.UUID(run_id))
        except Exception:
            await db.rollback()
            raise


async def classify_reply(ctx, reply_id: str) -> None:
    async with async_session_factory() as db:
        try:
            await classify_reply_by_id(db, reply_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def schedule_follow_up(ctx, run_id: str, campaign_id: str, org_id: str) -> None:
    async with async_session_factory() as db:
        from sqlalchemy import select

        from models.campaign import CampaignLead, LeadStatus

        try:
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
        except Exception:
            await db.rollback()
            raise


async def _run_agent_background(run_id: str) -> None:
    try:
        async with async_session_factory() as db:
            engine = AgentExecutionEngine(db)
            await engine.execute_run(uuid.UUID(run_id))
    except Exception:
        logger.exception("Background agent run %s failed", run_id)


async def enqueue_agent_run(run_id: str) -> None:
    if await redis_is_available():
        try:
            from services.scheduler.scheduler_service import get_arq_pool

            pool = await get_arq_pool()
            await pool.enqueue_job("execute_agent_run", run_id)
            return
        except Exception as exc:
            mark_redis_unavailable()
            logger.warning("Redis enqueue failed (%s); falling back in-process for run %s", exc, run_id)
    else:
        logger.info("Redis unavailable; scheduling agent run %s in-process", run_id)

    asyncio.create_task(_run_agent_background(run_id))


class WorkerSettings:
    functions = [execute_agent_run, classify_reply, schedule_follow_up]
    redis_settings = parse_redis_settings()
    max_jobs = 10
    job_timeout = 600

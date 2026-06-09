import asyncio
import logging

logger = logging.getLogger(__name__)


async def _classify_reply_background(reply_id: str) -> None:
    from agents.email_outreach.steps.follow_up import classify_reply_by_id
    from database import async_session_factory

    try:
        async with async_session_factory() as db:
            await classify_reply_by_id(db, reply_id)
            await db.commit()
    except Exception:
        logger.exception("Background reply classification failed for %s", reply_id)


async def enqueue_classify_reply(reply_id: str) -> None:
    try:
        from services.scheduler.scheduler_service import get_arq_pool

        pool = await get_arq_pool()
        await pool.enqueue_job("classify_reply", reply_id)
    except Exception as exc:
        logger.warning("Redis unavailable (%s); classifying reply %s in-process", exc, reply_id)
        asyncio.create_task(_classify_reply_background(reply_id))

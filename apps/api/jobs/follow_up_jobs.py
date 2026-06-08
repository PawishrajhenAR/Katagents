from jobs.tasks import enqueue_agent_run


async def enqueue_classify_reply(reply_id: str) -> None:
    from services.scheduler.scheduler_service import get_arq_pool

    pool = await get_arq_pool()
    await pool.enqueue_job("classify_reply", reply_id)

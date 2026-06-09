import logging

from arq import create_pool
from arq.connections import RedisSettings

from config import settings
from core.redis import mark_redis_unavailable, redis_is_available

logger = logging.getLogger(__name__)


def parse_redis_settings() -> RedisSettings:
    url = settings.redis_url
    if url.startswith("redis://"):
        parts = url.replace("redis://", "").split("/")
        host_port = parts[0]
        db = int(parts[1]) if len(parts) > 1 else 0
        if "@" in host_port:
            auth, host_port = host_port.rsplit("@", 1)
            password = auth.split(":")[-1] if ":" in auth else auth
        else:
            password = None
        host, port = host_port.split(":") if ":" in host_port else (host_port, 6379)
        return RedisSettings(host=host, port=int(port), database=db, password=password)
    return RedisSettings()


_pool = None


async def get_arq_pool():
    global _pool
    if _pool is None:
        _pool = await create_pool(parse_redis_settings())
    return _pool


class SchedulerService:
    async def enqueue_delayed(self, function_name: str, run_id: str, delay_seconds: int, **kwargs) -> bool:
        if not await redis_is_available():
            logger.warning("Redis unavailable; skipping delayed job %s", function_name)
            return False
        try:
            pool = await get_arq_pool()
            await pool.enqueue_job(function_name, run_id, **kwargs, _defer_by=delay_seconds)
            return True
        except Exception as exc:
            mark_redis_unavailable()
            logger.warning("Redis enqueue failed (%s); skipping delayed job %s", exc, function_name)
            return False

    async def enqueue_agent_run(self, run_id: str) -> bool:
        if not await redis_is_available():
            logger.warning("Redis unavailable; skipping agent run enqueue for %s", run_id)
            return False
        try:
            pool = await get_arq_pool()
            await pool.enqueue_job("execute_agent_run", run_id)
            return True
        except Exception as exc:
            mark_redis_unavailable()
            logger.warning("Redis enqueue failed (%s); skipping agent run %s", exc, run_id)
            return False

    async def enqueue_classify_reply(self, reply_id: str) -> bool:
        if not await redis_is_available():
            logger.warning("Redis unavailable; skipping classify reply enqueue for %s", reply_id)
            return False
        try:
            pool = await get_arq_pool()
            await pool.enqueue_job("classify_reply", reply_id)
            return True
        except Exception as exc:
            mark_redis_unavailable()
            logger.warning("Redis enqueue failed (%s); skipping classify reply %s", exc, reply_id)
            return False

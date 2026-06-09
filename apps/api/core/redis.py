import logging

from config import settings

logger = logging.getLogger(__name__)

_redis_available: bool | None = None


async def redis_is_available() -> bool:
    """Fast Redis probe — avoids arq's multi-second retry loop on every enqueue."""
    global _redis_available
    if _redis_available is not None:
        return _redis_available
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url, socket_connect_timeout=1)
        try:
            await client.ping()
            _redis_available = True
        finally:
            await client.aclose()
    except Exception:
        _redis_available = False
    return _redis_available


def mark_redis_unavailable() -> None:
    global _redis_available
    _redis_available = False

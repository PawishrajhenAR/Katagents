import time

from redis.asyncio import Redis

from config import settings

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


class RateLimitService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_limit(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        now = int(time.time())
        window_key = f"ratelimit:{key}:{now // window_seconds}"
        count = await self.redis.incr(window_key)
        if count == 1:
            await self.redis.expire(window_key, window_seconds)
        return count <= limit

    async def check_org_email_limit(self, org_id: str, daily_limit: int = 500) -> bool:
        return await self.check_limit(f"org_email:{org_id}", daily_limit, 86400)

    async def check_org_llm_limit(self, org_id: str, hourly_limit: int = 200) -> bool:
        return await self.check_limit(f"org_llm:{org_id}", hourly_limit, 3600)

    async def check_api_limit(self, user_id: str, limit: int = 100) -> bool:
        return await self.check_limit(f"api:{user_id}", limit, 60)


async def check_org_email_limit(org_id: str, daily_limit: int = 500) -> bool:
    try:
        redis = await get_redis()
        return await RateLimitService(redis).check_org_email_limit(org_id, daily_limit)
    except Exception:
        return True

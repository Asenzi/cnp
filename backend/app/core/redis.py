from redis.asyncio import Redis

from app.core.config import settings
from app.core.logger import logger

redis_client: Redis | None = None


async def init_redis() -> None:
    global redis_client

    if not settings.REDIS_ENABLED:
        logger.info("Redis is disabled by REDIS_ENABLED=false; skip initialization")
        return

    if redis_client is not None:
        return

    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    try:
        await redis_client.ping()
        logger.info("Redis connected")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Redis ping failed: {exc}")


def get_redis() -> Redis:
    if not settings.REDIS_ENABLED:
        raise RuntimeError("Redis is disabled by REDIS_ENABLED=false")

    if redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None

import logging

from arq.connections import RedisSettings, create_pool

from config import REDIS_URL

logger = logging.getLogger(__name__)


async def enqueue_turn(payload: dict) -> None:
    redis = None
    try:
        redis = await create_pool(RedisSettings.from_dsn(REDIS_URL))
        await redis.enqueue_job("persist_turn", payload)
    except Exception:
        logger.exception("Could not enqueue conversation persistence")
    finally:
        if redis is not None:
            await redis.aclose()

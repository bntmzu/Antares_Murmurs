import aioredis
import logging
from src.backend.config.settings import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self.redis = None

    async def connect(self):
        """Initialize Redis connection."""
        self.redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("Connected to Redis")

    async def set(self, key: str, value: str, expire: int = 3600):
        """Set a value in Redis with an expiration time."""
        if self.redis:
            await self.redis.set(key, value, ex=expire)
            logger.info(f" Cached {key} for {expire} seconds")

    async def get(self, key: str):
        """Get a value from Redis."""
        if self.redis:
            value = await self.redis.get(key)
            if value:
                logger.info(f" Cache hit for {key}")
            return value
        return None

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info(" Redis connection closed")


# Singleton instance
redis_client = RedisClient()

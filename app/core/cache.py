import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


class RedisCache:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def init_cache(self):
        """Initialize Redis connection"""
        self.redis = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        # Test connection
        await self.redis.ping()

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if self.redis:
            return await self.redis.get(key)
        return None

    async def set(self, key: str, value: str, expire: int = None) -> None:
        """Set value in cache"""
        if self.redis:
            expire = expire or settings.CACHE_EXPIRE_SECONDS
            await self.redis.setex(key, expire, value)

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(self, key: str, value: Any, expire: int = None) -> None:
        """Set JSON value in cache"""
        await self.set(key, json.dumps(value), expire)

    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        if self.redis:
            await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if self.redis:
            return await self.redis.exists(key) == 1
        return False

    async def clear_pattern(self, pattern: str) -> None:
        """Clear keys matching pattern"""
        if self.redis:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)


# Global cache instance
cache = RedisCache()

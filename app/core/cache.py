"""Redis and in-memory response caching configuration using fastapi-cache2.

Provides standard decorators (@cache) and Redis backend configuration to cache
frequent API responses, user balance queries, and status endpoints.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import redis.asyncio as aioredis

logger = logging.getLogger("cache")

# Default in-memory initialization ensures decorators never throw uninitialized errors
FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


async def init_cache(app: FastAPI, redis_url: Optional[str] = None) -> None:
    """Initialize FastAPICache with Redis backend or fallback to in-memory backend.

    Args:
        app: The FastAPI application instance
        redis_url: Optional Redis connection string (defaults to REDIS_URL environment variable)
    """
    target_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    is_testing = os.getenv("TESTING", "false").lower() in ("true", "1")

    if is_testing:
        logger.info("Initializing FastAPICache with InMemoryBackend (TESTING=true)")
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
        return

    try:
        redis_client = aioredis.from_url(
            target_url,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            decode_responses=False,
        )
        # Verify connectivity with Redis ping
        await redis_client.ping()
        FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
        logger.info("FastAPICache successfully initialized with Redis backend at %s", target_url)
    except Exception as exc:
        logger.warning(
            "Could not connect to Redis at %s (%s). Falling back to InMemoryBackend.",
            target_url,
            exc,
        )
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


__all__ = ["init_cache", "cache", "FastAPICache"]

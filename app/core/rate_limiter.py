"""Rate limiting configuration using the official slowapi library with Redis Token Bucket backend."""

from __future__ import annotations

import logging
import os
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logger = logging.getLogger("rate_limiter")


def get_client_identifier(request: Request) -> str:
    """Identify client by Authorization Bearer token if present, otherwise by IP address.

    Enables per-user rate limiting for authenticated SaaS subscribers and per-IP
    protection against unauthorized scrapers/DDoS attacks.
    """
    # 1. Check for Bearer token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token_prefix = auth_header.split(" ")[1][:16]
        return f"user_token:{token_prefix}"

    # 2. Check for forwarded client IP behind proxy (e.g. Nginx, Cloudflare)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # 3. Fallback to standard remote address
    return get_remote_address(request)


def resolve_storage_backend() -> str:
    """Determine whether to use Redis Token Bucket storage or in-memory fallback.

    Tests connectivity to Redis with a 1-second timeout. If Redis is unreachable
    (e.g. during local tests or offline dev), safely falls back to memory://.
    """
    if os.getenv("TESTING", "").lower() in ("true", "1", "yes"):
        return "memory://"

    redis_candidate = os.getenv("REDIS_URL", os.getenv("CELERY_BROKER_URL", ""))
    if not redis_candidate:
        return "memory://"

    try:
        import redis

        client = redis.from_url(redis_candidate, socket_timeout=0.5)
        client.ping()
        logger.info("Connected to Redis rate limit storage: %s", redis_candidate)
        return redis_candidate
    except Exception as exc:
        logger.info("Redis not reachable (%s); SlowAPI using in-memory token bucket.", exc)
        return "memory://"


# -----------------------------------------------------------------------------
# Limiter Initialization
# -----------------------------------------------------------------------------

storage_backend = resolve_storage_backend()

limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["120/minute"],
    storage_uri=storage_backend,
    strategy="moving-window",
)


# -----------------------------------------------------------------------------
# Standard RateLimitExceeded Exception Handler
# -----------------------------------------------------------------------------


def rate_limit_custom_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Standardized JSON response returning HTTP 429 Too Many Requests."""
    retry_after = getattr(exc, "retry_after", 60)
    detail_msg = getattr(exc, "detail", "Rate limit exceeded")
    logger.warning("Rate limit exceeded for %s on %s: %s", get_client_identifier(request), request.url.path, detail_msg)

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests to video generation pipeline: {detail_msg}.",
            "retry_after_seconds": retry_after,
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Exceeded": "true",
        },
    )

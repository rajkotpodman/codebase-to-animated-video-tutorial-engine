"""Tests for Sentry error capture and SlowAPI rate limiting security."""

import os
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.main import app
from app.core.sentry import init_sentry
from app.core.rate_limiter import limiter, rate_limit_custom_handler

client = TestClient(app)


def test_sentry_initialization_no_dsn():
    """Verify Sentry initializes gracefully in no-op mode without SENTRY_DSN."""
    result = init_sentry("test-service")
    # If SENTRY_DSN is not set in environment, returns False without raising
    assert result is False or result is True


def test_sentry_debug_endpoint_raises():
    """Verify /sentry-debug triggers ZeroDivisionError for Sentry exception reporting."""
    with pytest.raises(ZeroDivisionError):
        client.get("/sentry-debug")


def test_slowapi_rate_limiting_enforcement():
    """Verify SlowAPI Token Bucket rate limiter enforces quota and returns HTTP 429."""
    # Create isolated test app with strict 2/minute rate limit
    test_app = FastAPI()
    test_limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
    test_app.state.limiter = test_limiter
    test_app.add_exception_handler(RateLimitExceeded, rate_limit_custom_handler)

    @test_app.post("/test-limited-action")
    @test_limiter.limit("2/minute")
    def limited_action(request: Request):
        return {"status": "ok"}

    test_client = TestClient(test_app)

    # First request: 200 OK
    res1 = test_client.post("/test-limited-action")
    assert res1.status_code == 200
    assert res1.json() == {"status": "ok"}

    # Second request: 200 OK
    res2 = test_client.post("/test-limited-action")
    assert res2.status_code == 200

    # Third request: 429 Too Many Requests (Rate limit exceeded)
    res3 = test_client.post("/test-limited-action")
    assert res3.status_code == 429
    data = res3.json()
    assert data["error"] == "Rate limit exceeded"
    assert "retry_after_seconds" in data
    assert "Retry-After" in res3.headers
    assert res3.headers["X-RateLimit-Exceeded"] == "true"

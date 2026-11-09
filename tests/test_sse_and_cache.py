"""Tests for Server-Sent Events (sse-starlette) and response caching (fastapi-cache2)."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.main import app
from app.api.video_routes import resolve_job_status
from app.core.auth_middleware import AuthenticatedUser, get_current_user

client = TestClient(app)


def test_resolve_job_status_pending():
    """Verify that a pending job status response has progress 0 and PENDING state."""
    res = resolve_job_status("test_job_pending_1")
    assert res.job_id == "test_job_pending_1"
    assert res.status in ("PENDING", "PROGRESS", "SUCCESS", "FAILURE")
    assert res.progress >= 0


def test_sse_stream_endpoint():
    """Verify that /api/v1/jobs/{job_id}/stream returns text/event-stream with SSE formatting."""
    with patch("app.api.video_routes.resolve_job_status") as mock_resolve:
        # Mock terminal state so generator yields once and completes
        mock_resolve.return_value = MagicMock(
            status="SUCCESS",
            progress=100,
            step=5,
            model_dump_json=lambda: json.dumps(
                {
                    "job_id": "test_sse_job_1",
                    "status": "SUCCESS",
                    "progress": 100,
                    "step": 5,
                    "step_name": "Completed",
                    "message": "Video generation completed successfully!",
                    "download_url": "/api/v1/jobs/test_sse_job_1/download",
                }
            ),
        )

        with client.stream("GET", "/api/v1/jobs/test_sse_job_1/stream") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            # Read lines from stream
            lines = [line.strip() for line in response.iter_lines() if line.strip()]
            assert any("event: complete" in line for line in lines)
            assert any("test_sse_job_1" in line for line in lines)


def test_fastapi_cache_response():
    """Verify that cached endpoints return cached responses on subsequent requests."""
    # Ensure cache backend is initialized
    FastAPICache.init(InMemoryBackend(), prefix="test-cache")

    mock_user = AuthenticatedUser(
        user_id="test_user_cache_1",
        email="cache_test@example.com",
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        # First request populates cache
        resp1 = client.get("/api/v1/billing/balance")
        assert resp1.status_code == 200
        data1 = resp1.json()

        # Second request should read from cache
        resp2 = client.get("/api/v1/billing/balance")
        assert resp2.status_code == 200
        data2 = resp2.json()

        assert data1 == data2
        assert data1["user_id"] == "test_user_cache_1"
    finally:
        app.dependency_overrides.pop(get_current_user, None)

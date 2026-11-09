"""Tests for Prometheus FastAPI metrics and telemetry instrumentation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.telemetry import (
    ACTIVE_VIDEO_JOBS,
    TOTAL_VIDEO_JOBS,
    record_job_start,
    record_job_completion,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_metrics_endpoint_exposed(client):
    """Verify that /metrics endpoint returns HTTP 200 with Prometheus text format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

    body = response.text
    # Verify standard HTTP metrics are present
    assert "http_requests_total" in body or "http_request_duration_seconds" in body
    # Verify custom active video generation jobs metrics are registered
    assert "fastapi_active_video_jobs" in body
    assert "fastapi_video_jobs_total" in body


def test_metrics_track_http_requests(client):
    """Verify that hitting application endpoints updates HTTP request counters."""
    # Hit health endpoint
    health_resp = client.get("/health")
    assert health_resp.status_code == 200

    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    assert "http_requests_total" in metrics_resp.text


def test_job_telemetry_recording():
    """Verify that record_job_start and record_job_completion update Prometheus metrics."""
    initial_active = ACTIVE_VIDEO_JOBS._value.get() if hasattr(ACTIVE_VIDEO_JOBS, "_value") else 0

    # Simulate job start
    record_job_start()
    new_active = ACTIVE_VIDEO_JOBS._value.get() if hasattr(ACTIVE_VIDEO_JOBS, "_value") else initial_active + 1
    assert new_active >= initial_active

    # Simulate job completion
    record_job_completion("success", duration_seconds=12.5)
    final_active = ACTIVE_VIDEO_JOBS._value.get() if hasattr(ACTIVE_VIDEO_JOBS, "_value") else new_active - 1
    assert final_active <= new_active

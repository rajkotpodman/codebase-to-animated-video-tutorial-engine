"""Asynchronous unit tests for FastAPI endpoints and Celery workers.

Uses industry-standard open-source testing libraries:
  - pytest-asyncio (@pytest.mark.asyncio)
  - httpx (httpx.AsyncClient & ASGITransport)
  - pytest-mock (mocker fixture)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pytest_mock import MockerFixture

from app.main import app
from app.core.auth_middleware import AuthenticatedUser, get_current_user
from app.workers.celery_worker import celery_app
from app.workers.tasks import generate_video_pipeline, run_video_pipeline_sync

# -----------------------------------------------------------------------------
# Pytest Async Fixtures
# -----------------------------------------------------------------------------


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Yield an asynchronous httpx client bound to the FastAPI ASGI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def mock_auth_user():
    """Provides a mock authenticated user fixture."""
    return AuthenticatedUser(
        user_id="user_qa_tester_01",
        email="qa-tester@example.com",
        role="authenticated",
    )


# -----------------------------------------------------------------------------
# 1. Asynchronous FastAPI Endpoint Tests (httpx + pytest-asyncio)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_health_and_root_endpoints(async_client: AsyncClient):
    """Verify health check and root service discovery asynchronously."""
    # Test Liveness Probe
    resp_health = await async_client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json() == {"status": "healthy"}

    # Test Root Service Metadata
    resp_root = await async_client.get("/")
    assert resp_root.status_code == 200
    data = resp_root.json()
    assert data["service"] == "Codebase-to-Animated Video Tutorial Engine"
    assert "scalar_docs" in data["endpoints"]
    assert data["endpoints"]["scalar_docs"] == "/scalar"


@pytest.mark.asyncio
async def test_async_scalar_api_reference_ui(async_client: AsyncClient):
    """Verify that Scalar FastAPI interactive documentation UI renders successfully."""
    response = await async_client.get("/scalar")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    html_content = response.text
    # Verify essential Scalar CDN bundle and configuration
    assert "@scalar/api-reference" in html_content
    assert "openapi.json" in html_content
    assert "Scalar Interactive API Reference" in html_content


@pytest.mark.asyncio
async def test_async_generate_video_validation_error(async_client: AsyncClient):
    """Verify request validation rejects invalid resolution or missing repo."""
    invalid_payload = {
        "repo_url": "octocat/Hello-World",
        "resolution": "4k_ultra_hd",  # Invalid resolution literal
    }
    response = await async_client.post("/api/v1/generate-video", json=invalid_payload)
    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any("resolution" in str(err) for err in errors)


@pytest.mark.asyncio
async def test_async_generate_video_dispatch_success(
    async_client: AsyncClient,
    mocker: MockerFixture,
):
    """Verify video generation job dispatch via mocked Celery delay."""
    # Mock celery task dispatch
    mock_task = MagicMock()
    mock_task.id = "async_job_test_12345"
    mocker.patch.object(generate_video_pipeline, "delay", return_value=mock_task)

    payload = {
        "repo_url": "https://github.com/fastapi/fastapi",
        "voice": "en-US-GuyNeural",
        "resolution": "1080p",
        "theme": "midnight",
        "burn_subtitles": True,
    }

    response = await async_client.post("/api/v1/generate-video", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == "async_job_test_12345"
    assert data["status"] == "QUEUED"
    assert "/api/v1/jobs/async_job_test_12345" in data["status_url"]


@pytest.mark.asyncio
async def test_async_sse_progress_stream(
    async_client: AsyncClient,
    mocker: MockerFixture,
):
    """Verify Server-Sent Events stream yields real-time progress updates."""
    # Mock resolve_job_status to yield a terminal completed event
    mock_status = MagicMock(
        status="SUCCESS",
        progress=100,
        step=5,
        step_name="Completed",
        model_dump_json=lambda: json.dumps(
            {
                "job_id": "job_sse_async_99",
                "status": "SUCCESS",
                "progress": 100,
                "step": 5,
                "step_name": "Completed",
                "message": "Render completed successfully!",
                "download_url": "/api/v1/jobs/job_sse_async_99/download",
            }
        ),
    )
    mocker.patch("app.api.video_routes.resolve_job_status", return_value=mock_status)

    async with async_client.stream("GET", "/api/v1/jobs/job_sse_async_99/stream") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        events_received = []
        async for line in response.aiter_lines():
            if line.strip():
                events_received.append(line.strip())
            if len(events_received) >= 4:
                break

        assert any("event: complete" in line for line in events_received)
        assert any("job_sse_async_99" in line for line in events_received)


@pytest.mark.asyncio
async def test_async_billing_balance_with_auth(
    async_client: AsyncClient,
    mock_auth_user: AuthenticatedUser,
):
    """Verify authenticated user balance query with fastapi-cache2 caching."""
    app.dependency_overrides[get_current_user] = lambda: mock_auth_user
    try:
        resp = await async_client.get("/api/v1/billing/balance")
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == mock_auth_user.user_id
        assert body["email"] == mock_auth_user.email
        assert body["credits"] >= 0
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# -----------------------------------------------------------------------------
# 2. Celery Worker Pipeline Unit Tests (pytest-mock)
# -----------------------------------------------------------------------------


def test_celery_worker_task_success(mocker: MockerFixture):
    """Test Celery pipeline task execution and metrics recording on success."""
    mock_pipeline_result = {
        "status": "SUCCESS",
        "job_id": "test_celery_mock_job_1",
        "repo_url": "octocat/Hello-World",
        "repo_name": "Hello-World",
        "final_video_path": "output_artifacts/final_test.mp4",
        "duration_seconds": 32.5,
        "resolution": "1920x1080",
        "file_size_bytes": 1048576,
        "subtitles_burned": True,
        "srt_path": "output_artifacts/test.srt",
        "audio_path": "output_artifacts/test.mp3",
        "total_files_packed": 4,
        "model_used": "gemini-2.5-flash",
        "elapsed_seconds": 12.4,
    }

    mock_run_sync = mocker.patch(
        "app.workers.tasks.run_video_pipeline_sync",
        return_value=mock_pipeline_result,
    )
    mock_telemetry_complete = mocker.patch("app.workers.tasks.record_job_completion")

    # Execute task synchronously via Celery's standard apply() test method
    async_res = generate_video_pipeline.apply(
        args=["octocat/Hello-World"],
        kwargs={"options": {"resolution": "1080p"}},
        task_id="test_celery_mock_job_1",
    )
    result = async_res.result

    assert result["status"] == "SUCCESS"
    assert result["job_id"] == "test_celery_mock_job_1"
    assert result["duration_seconds"] == 32.5

    mock_run_sync.assert_called_once()
    mock_telemetry_complete.assert_called_once()
    assert mock_telemetry_complete.call_args[0][0] == "success"


def test_celery_worker_task_failure_sentry_capture(mocker: MockerFixture):
    """Test Celery pipeline task exception handling, Sentry capture, and telemetry."""
    mocker.patch(
        "app.workers.tasks.run_video_pipeline_sync",
        side_effect=RuntimeError("Simulated pipeline GPU render crash"),
    )
    mock_sentry = mocker.patch("app.workers.tasks.capture_sentry_exception")
    mock_telemetry_complete = mocker.patch("app.workers.tasks.record_job_completion")

    with pytest.raises(RuntimeError, match="Simulated pipeline GPU render crash"):
        generate_video_pipeline.apply(
            args=["broken/repo"],
            kwargs={"options": {}},
            task_id="failed_job_404",
        ).get()

    # Verify Sentry exception capture was triggered with job context
    mock_sentry.assert_called_once()
    # Verify telemetry completion was recorded as failure
    mock_telemetry_complete.assert_called_once()
    assert mock_telemetry_complete.call_args[0][0] == "failure"

"""Unit tests for structlog structured JSON logging integration."""

from __future__ import annotations

import json
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
import structlog

from app.core.logging import (
    StructlogRequestMiddleware,
    get_logger,
    setup_celery_logging,
    setup_logging,
)
from app.main import app


def test_structlog_setup_configuration():
    """Verify setup_logging properly configures structlog and standard library logging."""
    setup_logging(service_name="test-service", log_level="DEBUG")
    logger = get_logger("test.logger")
    assert logger is not None


def test_request_id_middleware_generated_header():
    """Verify that incoming requests without X-Request-ID receive a generated request ID."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert request_id.startswith("req_")


def test_request_id_middleware_preserves_client_header():
    """Verify that incoming client-supplied X-Request-ID is preserved and propagated."""
    client = TestClient(app)
    custom_req_id = "custom_trace_id_998877"
    response = client.get("/health", headers={"X-Request-ID": custom_req_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_req_id


def test_structlog_contextvars_binding():
    """Verify that context variables are captured in structured log dicts."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id="req_test_ctx_01",
        job_id="job_test_ctx_02",
    )

    ctx = structlog.contextvars.get_contextvars()
    assert ctx["request_id"] == "req_test_ctx_01"
    assert ctx["job_id"] == "job_test_ctx_02"

    structlog.contextvars.clear_contextvars()
    assert structlog.contextvars.get_contextvars() == {}


def test_celery_logging_signal_handlers(mocker: MockerFixture):
    """Verify Celery task signals bind task_id and task_name to contextvars."""
    setup_celery_logging()

    # Test Celery prerun signal
    from celery.signals import task_failure, task_postrun, task_prerun

    mock_task = MagicMock()
    mock_task.name = "generate_video_pipeline"

    # Send prerun signal
    task_prerun.send(
        sender=mock_task,
        task_id="celery_task_12345",
        task=mock_task,
        args=[],
        kwargs={},
    )

    ctx = structlog.contextvars.get_contextvars()
    assert ctx.get("task_id") == "celery_task_12345"
    assert ctx.get("task_name") == "generate_video_pipeline"

    # Send postrun signal
    task_postrun.send(
        sender=mock_task,
        task_id="celery_task_12345",
        task=mock_task,
        args=[],
        kwargs={},
        retval={},
        state="SUCCESS",
    )

    # Postrun clears contextvars
    ctx_after = structlog.contextvars.get_contextvars()
    assert "task_id" not in ctx_after

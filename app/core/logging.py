"""Structured JSON logging configuration using structlog for FastAPI and Celery.

Provides contextual timestamps, request IDs, log levels, caller information,
and exception tracing formatted for cloud log aggregators (e.g., Datadog, Loki, CloudWatch).
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from typing import Any, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog


def setup_logging(
    service_name: str = "fastapi-backend",
    log_level: Optional[str] = None,
) -> None:
    """Configure structlog and redirect standard library logging to structured JSON output.

    Args:
        service_name: Name of the service component (e.g. 'fastapi-backend', 'celery-worker')
        log_level: Desired log level (e.g. 'INFO', 'DEBUG'). Defaults to LOG_LEVEL env var or 'INFO'.
    """
    level_str = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_str, logging.INFO)

    # Use JSON formatting by default; allow console pretty-printing if explicitly requested
    log_format = os.getenv("LOG_FORMAT", "json").lower()
    is_json = log_format != "console"

    # Shared processors for both structlog and standard library logging
    shared_processors: list[Callable[..., Any]] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer = structlog.processors.JSONRenderer() if is_json else structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging handler
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Pre-bind service component name in contextvars
    structlog.contextvars.bind_contextvars(service=service_name)


class StructlogRequestMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware that binds request IDs and logs incoming HTTP requests."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        # Clear any leftover context from previous requests on the same thread/worker
        structlog.contextvars.clear_contextvars()

        # Extract or generate unique X-Request-ID
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        client_ip = request.client.host if request.client else "unknown"

        # Bind contextual attributes to structlog contextvars
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            http_method=request.method,
            http_path=request.url.path,
            client_ip=client_ip,
        )

        logger = structlog.get_logger("fastapi.access")
        start_time = time.perf_counter()

        logger.info(
            "HTTP request started",
            path=request.url.path,
            method=request.method,
        )

        try:
            response: Response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                "HTTP request completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "HTTP request failed with unhandled exception",
                error=str(exc),
                duration_ms=duration_ms,
            )
            raise


def setup_celery_logging() -> None:
    """Connect Celery task signals to automatically bind task_id and task_name to structlog contextvars."""
    try:
        from celery.signals import task_failure, task_postrun, task_prerun

        @task_prerun.connect(weak=False)
        def on_task_prerun(sender: Any = None, task_id: Optional[str] = None, task: Any = None, **kwargs: Any) -> None:
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(
                task_id=task_id or "unknown",
                task_name=getattr(task, "name", "unknown_task"),
            )
            logger = structlog.get_logger("celery.task")
            logger.info("Celery task started", task_id=task_id, task_name=getattr(task, "name", "unknown_task"))

        @task_postrun.connect(weak=False)
        def on_task_postrun(
            sender: Any = None, task_id: Optional[str] = None, task: Any = None, state: str = "UNKNOWN", **kwargs: Any
        ) -> None:
            logger = structlog.get_logger("celery.task")
            logger.info("Celery task completed", task_id=task_id, state=state)
            structlog.contextvars.clear_contextvars()

        @task_failure.connect(weak=False)
        def on_task_failure(
            sender: Any = None, task_id: Optional[str] = None, exception: Optional[Exception] = None, **kwargs: Any
        ) -> None:
            logger = structlog.get_logger("celery.task")
            logger.error("Celery task failed with exception", task_id=task_id, error=str(exception))
            structlog.contextvars.clear_contextvars()

    except ImportError:
        pass


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Convenience accessor to obtain a configured structlog logger instance."""
    return structlog.get_logger(name)


__all__ = [
    "setup_logging",
    "StructlogRequestMiddleware",
    "setup_celery_logging",
    "get_logger",
]

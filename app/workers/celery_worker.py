"""Celery application and configuration for asynchronous background tasks.

Configured with Redis for message brokering and state persistence.
Optimized for Windows and Linux worker execution.
"""

from __future__ import annotations

import os
from celery import Celery
from app.core.sentry import init_sentry
from app.core.logging import setup_logging, setup_celery_logging

# Initialize structured JSON logging (structlog) for Celery worker
setup_logging(service_name="celery-worker")
setup_celery_logging()

# Initialize Sentry for Celery Worker tasks and error reporting
init_sentry(service_name="celery-worker")

# Redis configuration from environment variables with sensible defaults
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

celery_app = Celery(
    "codebase_video_engine",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.workers.tasks"],
)

# Celery Performance & Reliability Settings
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30-minute maximum runtime per job
    task_soft_time_limit=1500,  # 25-minute soft warning limit
    worker_prefetch_multiplier=1,
    result_expires=86400,  # Persist task results for 24 hours
    # Enable eager mode if requested via environment (ideal for unit testing without live Redis)
    task_always_eager=os.environ.get("CELERY_TASK_ALWAYS_EAGER", "false").lower() in ("true", "1", "yes"),
)

# Windows-safe worker pool configuration (Windows lacks native POSIX fork)
if os.name == "nt":
    celery_app.conf.update(
        worker_pool="threads",
        worker_concurrency=int(os.environ.get("CELERY_CONCURRENCY", "4")),
    )

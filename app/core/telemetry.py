"""Prometheus metrics and observability for FastAPI and pipeline workers.

Uses the official open-source 'prometheus-fastapi-instrumentator' package to track:
  - HTTP request durations (latency percentiles)
  - HTTP response statuses and throughput
  - Active and total video generation jobs ready for Grafana dashboards
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import FastAPI
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator, metrics

logger = logging.getLogger("telemetry")


# -----------------------------------------------------------------------------
# Safe Metric Registry Helpers (Idempotent across test reloads)
# -----------------------------------------------------------------------------


def _get_or_create_metric(collector_cls, name: str, documentation: str, **kwargs):
    """Safely retrieves an existing metric or creates a new one to prevent registry collisions."""
    existing = REGISTRY._names_to_collectors.get(name)
    if existing is not None:
        return existing
    try:
        return collector_cls(name, documentation, **kwargs)
    except ValueError:
        # Fallback if another thread registered it concurrently
        return REGISTRY._names_to_collectors.get(name)


# -----------------------------------------------------------------------------
# Prometheus Video Pipeline Metrics (Grafana Ready)
# -----------------------------------------------------------------------------

ACTIVE_VIDEO_JOBS = _get_or_create_metric(
    Gauge,
    "fastapi_active_video_jobs",
    "Current number of video generation jobs actively running in the pipeline",
)

TOTAL_VIDEO_JOBS = _get_or_create_metric(
    Counter,
    "fastapi_video_jobs_total",
    "Total video generation jobs submitted by outcome status",
    labelnames=["status"],
)

PIPELINE_DURATION_SECONDS = _get_or_create_metric(
    Histogram,
    "fastapi_video_pipeline_duration_seconds",
    "End-to-end execution duration for video generation jobs in seconds",
    buckets=(10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)


# -----------------------------------------------------------------------------
# Tracking Utility Functions
# -----------------------------------------------------------------------------


def record_job_start() -> None:
    """Increment active job gauge and queued counter."""
    try:
        ACTIVE_VIDEO_JOBS.inc()
        TOTAL_VIDEO_JOBS.labels(status="queued").inc()
    except Exception as exc:
        logger.debug("Failed to record job start metric: %s", exc)


def record_job_completion(status: str, duration_seconds: Optional[float] = None) -> None:
    """Decrement active job gauge and record outcome status and latency."""
    try:
        ACTIVE_VIDEO_JOBS.dec()
        TOTAL_VIDEO_JOBS.labels(status=status).inc()
        if duration_seconds is not None and duration_seconds > 0:
            PIPELINE_DURATION_SECONDS.observe(duration_seconds)
    except Exception as exc:
        logger.debug("Failed to record job completion metric: %s", exc)


# -----------------------------------------------------------------------------
# FastApi Setup & Instrumentation
# -----------------------------------------------------------------------------


def setup_telemetry(app: FastAPI) -> Instrumentator:
    """Instrument the FastAPI application and expose the standard /metrics endpoint.

    Configured out-of-the-box with:
      - HTTP request duration histograms (p50, p95, p99)
      - HTTP request throughput grouped by method, path, and HTTP status code
      - Request/response payload sizes in bytes
      - Standard Python runtime GC, memory, and thread metrics
    """
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/sentry-debug"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    ).add(metrics.default())

    instrumentator.instrument(app)
    instrumentator.expose(
        app,
        endpoint="/metrics",
        tags=["Observability"],
        include_in_schema=True,
        should_gzip=False,
    )

    logger.info("Prometheus FastAPI Instrumentator active at /metrics")
    return instrumentator

"""Official Sentry SDK integration for FastAPI backend and Celery worker observability."""

from __future__ import annotations

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger("sentry_integration")

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = os.getenv("ENVIRONMENT", os.getenv("SENTRY_ENVIRONMENT", "development"))
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.2"))


def init_sentry(service_name: str = "fastapi-backend") -> bool:
    """Initialize Sentry SDK with FastAPI and Celery integrations.

    Parameters
    ----------
    service_name : str
        Identifying service tag ('fastapi-backend' or 'celery-worker').

    Returns
    -------
    bool
        True if Sentry was initialized with a valid DSN, False otherwise.
    """
    if not SENTRY_DSN:
        logger.info("SENTRY_DSN not provided. Sentry telemetry disabled for %s.", service_name)
        return False

    try:
        # Standard logging integration capturing warnings and errors as breadcrumbs/events
        logging_integration = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENVIRONMENT,
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                CeleryIntegration(monitor_beat_tasks=True),
                logging_integration,
            ],
            send_default_pii=True,
            attach_stacktrace=True,
        )

        sentry_sdk.set_tag("service", service_name)
        logger.info("Sentry initialized successfully for %s in '%s' environment.", service_name, SENTRY_ENVIRONMENT)
        return True
    except Exception as exc:
        logger.warning("Failed to initialize Sentry for %s: %s", service_name, exc)
        return False


def capture_sentry_exception(exc: Exception, **tags: str) -> None:
    """Safely capture and send an exception to Sentry with contextual tags."""
    if SENTRY_DSN:
        with sentry_sdk.push_scope() as scope:
            for k, v in tags.items():
                scope.set_tag(k, v)
            sentry_sdk.capture_exception(exc)


def add_sentry_breadcrumb(category: str, message: str, level: str = "info", **data) -> None:
    """Add a structured breadcrumb to Sentry trace context."""
    if SENTRY_DSN:
        sentry_sdk.add_breadcrumb(
            category=category,
            message=message,
            level=level,
            data=data,
        )

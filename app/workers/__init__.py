"""Asynchronous worker package for pipeline execution."""

from app.workers.celery_worker import celery_app

__all__ = ["celery_app"]

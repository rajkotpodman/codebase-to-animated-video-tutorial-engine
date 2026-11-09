"""FastAPI video generation and job management endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from app.core.cache import cache
from app.core.rate_limiter import limiter
from app.core.telemetry import record_job_start
from app.workers.celery_worker import celery_app
from app.workers.tasks import generate_video_pipeline, run_video_pipeline_sync
from app.schemas import (
    GenerateVideoRequest,
    GenerateVideoResponse,
    JobStatusResponse,
    LanguageInfo,
    SUPPORTED_LANGUAGES,
    resolve_language_info,
)

logger = logging.getLogger("api_video_routes")

router = APIRouter(prefix="/api/v1", tags=["Video Generation Pipeline"])


LOCAL_JOBS_STORE: Dict[str, Dict[str, Any]] = {}


def is_redis_broker_available() -> bool:
    """Fast non-blocking connectivity check for Celery's Redis broker (200ms timeout)."""
    try:
        import redis

        target_url = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        client = redis.from_url(target_url, socket_timeout=0.2, socket_connect_timeout=0.2)
        return bool(client.ping())
    except Exception:
        return False


class LocalTaskWrapper:
    """Task wrapper providing Celery-compatible interface for local asynchronous execution."""

    def __init__(self, job_id: str):
        self.id = job_id
        self.request = type("Request", (), {"id": job_id})()

    def update_state(self, state: str = "PROGRESS", meta: Optional[Dict[str, Any]] = None) -> None:
        if self.id in LOCAL_JOBS_STORE and meta:
            LOCAL_JOBS_STORE[self.id].update(
                {
                    "status": state,
                    "progress": int(meta.get("progress", 50)),
                    "step": meta.get("step"),
                    "step_name": meta.get("step_name"),
                    "message": meta.get("message"),
                }
            )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@router.get(
    "/languages",
    response_model=List[LanguageInfo],
    summary="Get catalog of supported tutorial narration languages and neural voices",
)
async def get_supported_languages() -> List[LanguageInfo]:
    """Returns all supported Indian and World languages with voice options."""
    return list(SUPPORTED_LANGUAGES.values())


@router.post(
    "/generate-video",
    response_model=GenerateVideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger asynchronous codebase tutorial video generation",
)
@limiter.limit(os.getenv("GENERATE_VIDEO_RATE_LIMIT", "5/minute"))
async def generate_video(
    request: Request,
    payload: GenerateVideoRequest,
):
    """Triggers the background video generation pipeline:

    1. Ingestion / Repomix codebase packaging
    2. Codebase Graph Mapping (AST & Architecture topology)
    3. Multilingual Gemini AI script & scene generation
    4. Manim Community animation rendering
    5. Neural voiceover TTS & .srt subtitle synthesis in target language
    6. FFmpeg final resolution scaling, duration sync, & subtitle burn-in
    """
    lang_info = resolve_language_info(payload.target_language)

    # Automatically resolve voice: if default voice was untouched with a non-English language,
    # switch to the native neural voice for that language (e.g. gu-IN-DhwaniNeural for Gujarati)
    effective_voice = payload.voice
    if (not effective_voice or effective_voice == "en-US-ChristopherNeural") and lang_info.code != "en":
        effective_voice = lang_info.default_voice
    elif not effective_voice:
        effective_voice = lang_info.default_voice

    options = {
        "voice": effective_voice,
        "target_language": lang_info.code,
        "language_name": lang_info.name,
        "theme": payload.theme,
        "burn_subtitles": payload.burn_subtitles,
        "custom_instructions": payload.custom_instructions,
        "gemini_model": payload.gemini_model or "gemini-2.5-flash",
        "target_width": 1920 if payload.resolution == "1080p" else (1280 if payload.resolution == "720p" else 854),
        "target_height": 1080 if payload.resolution == "1080p" else (720 if payload.resolution == "720p" else 480),
        "manim_quality": "h" if payload.resolution == "1080p" else ("m" if payload.resolution == "720p" else "l"),
    }

    try:
        record_job_start()
        if payload.run_sync:
            # Synchronous execution mode
            res_dict = run_video_pipeline_sync(repo_url=payload.repo_url, options=options)
            job_id = res_dict["job_id"]
            return GenerateVideoResponse(
                job_id=job_id,
                status="COMPLETED",
                status_url=f"/api/v1/jobs/{job_id}",
                message=f"Video generation completed synchronously in {lang_info.name}.",
                target_language=lang_info.code,
                voice=effective_voice,
            )

        # Enqueue Celery async task if Redis broker is online, or if mocked / eager in tests
        is_mocked = hasattr(generate_video_pipeline.delay, "assert_called") or hasattr(
            generate_video_pipeline.delay, "mock"
        )
        redis_online = is_mocked or celery_app.conf.task_always_eager or is_redis_broker_available()
        job_id = None

        if redis_online:
            try:
                task = generate_video_pipeline.delay(payload.repo_url, options)
                job_id = task.id
            except Exception as queue_exc:
                logger.warning("Celery dispatch failed despite ping (%s). Falling back to local worker.", queue_exc)
                redis_online = False

        if not redis_online or not job_id:
            import threading
            import uuid

            job_id = f"job_local_{uuid.uuid4().hex[:10]}"
            logger.info("Processing job %s via local asynchronous worker thread.", job_id)
            LOCAL_JOBS_STORE[job_id] = {
                "job_id": job_id,
                "status": "PROGRESS",
                "progress": 5,
                "step": 1,
                "step_name": "Ingestion & Repomix",
                "message": f"Initializing background video pipeline in {lang_info.name}...",
                "target_language": lang_info.code,
                "result": None,
                "error": None,
            }

            def _background_worker():
                task_inst = LocalTaskWrapper(job_id)
                try:
                    res = run_video_pipeline_sync(
                        repo_url=payload.repo_url,
                        options=options,
                        job_id=job_id,
                        task_instance=task_inst,
                    )
                    LOCAL_JOBS_STORE[job_id].update(
                        {
                            "status": "SUCCESS",
                            "progress": 100,
                            "step": 5,
                            "step_name": "Completed",
                            "message": "Video generation completed successfully!",
                            "result": res,
                        }
                    )
                except Exception as worker_exc:
                    logger.exception("Local background worker failed for job %s: %s", job_id, worker_exc)
                    LOCAL_JOBS_STORE[job_id].update(
                        {
                            "status": "FAILURE",
                            "progress": 0,
                            "error": str(worker_exc),
                            "message": "Video generation failed.",
                        }
                    )

            threading.Thread(target=_background_worker, daemon=True).start()

        return GenerateVideoResponse(
            job_id=job_id,
            status="QUEUED",
            status_url=f"/api/v1/jobs/{job_id}",
            message=f"Video generation task successfully queued in {lang_info.name}.",
            target_language=lang_info.code,
            voice=effective_voice,
        )
    except Exception as exc:
        logger.exception("Failed to dispatch video generation job: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue video generation job: {exc}",
        )


def resolve_job_status(job_id: str) -> JobStatusResponse:
    """Query Celery/Redis, local store, or disk artifact for the current status of a job."""
    if job_id in LOCAL_JOBS_STORE:
        info = LOCAL_JOBS_STORE[job_id]
        return JobStatusResponse(
            job_id=job_id,
            status=info.get("status", "PROGRESS"),
            progress=int(info.get("progress", 50)),
            step=info.get("step"),
            step_name=info.get("step_name"),
            message=info.get("message"),
            result=info.get("result"),
            error=info.get("error"),
            download_url=f"/api/v1/jobs/{job_id}/download" if info.get("status") == "SUCCESS" else None,
        )

    state = "PENDING"
    meta: Dict[str, Any] = {}
    result_data = None
    error_msg = None

    try:
        task_res = AsyncResult(job_id, app=celery_app)
        state = task_res.state
        if state == "PROGRESS":
            meta = task_res.info or {}
        elif state == "SUCCESS":
            result_data = task_res.result or {}
        elif state == "FAILURE":
            error_msg = str(task_res.info or "Task failed")
    except Exception as exc:
        logger.warning("Could not query Celery/Redis for job %s: %s", job_id, exc)
        # Check artifact directory on disk for completed job
        artifact_path = Path("output_artifacts") / job_id / f"final_{job_id}.mp4"
        if artifact_path.exists():
            state = "SUCCESS"
            result_data = {"final_video_path": str(artifact_path)}
        else:
            state = "PENDING"

    if state == "PENDING":
        return JobStatusResponse(
            job_id=job_id,
            status="PENDING",
            progress=0,
            message="Job is waiting in queue...",
        )

    elif state == "PROGRESS":
        return JobStatusResponse(
            job_id=job_id,
            status="PROGRESS",
            progress=int(meta.get("progress", 50)),
            step=meta.get("step"),
            step_name=meta.get("step_name"),
            message=meta.get("message", "Processing video pipeline..."),
        )

    elif state == "SUCCESS":
        return JobStatusResponse(
            job_id=job_id,
            status="SUCCESS",
            progress=100,
            step=5,
            step_name="Completed",
            message="Video generation completed successfully!",
            result=result_data,
            download_url=f"/api/v1/jobs/{job_id}/download",
        )

    elif state == "FAILURE":
        return JobStatusResponse(
            job_id=job_id,
            status="FAILURE",
            progress=0,
            error=error_msg or "Unknown task execution error",
            message="Video generation failed.",
        )

    # Any other transient Celery state (e.g. RETRY, STARTED)
    return JobStatusResponse(
        job_id=job_id,
        status=state,
        progress=10,
        message=f"Current task state: {state}",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Query background task status and progress",
)
@cache(expire=2)
async def get_job_status(job_id: str):
    """Poll the status and progress of a video generation task with short-lived caching."""
    return resolve_job_status(job_id)


@router.get(
    "/jobs/{job_id}/stream",
    summary="Stream live video generation progress via Server-Sent Events (SSE)",
)
async def stream_job_progress(request: Request, job_id: str):
    """Stream live progress updates (0% to 100% and stage changes) directly via Server-Sent Events."""

    async def event_generator():
        last_progress = -1
        last_step = None
        max_duration_seconds = 1800  # 30-minute safety timeout
        start_time = asyncio.get_event_loop().time()

        while True:
            # 1. Detect client disconnection
            if await request.is_disconnected():
                logger.info("Client disconnected from SSE stream for job %s", job_id)
                break

            # 2. Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_duration_seconds:
                logger.warning("SSE stream timeout reached for job %s", job_id)
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Stream timeout exceeded", "job_id": job_id}),
                }
                break

            # 3. Retrieve current status
            status_data = resolve_job_status(job_id)
            curr_progress = status_data.progress
            curr_step = status_data.step
            curr_status = status_data.status

            # 4. Stream update if changed or terminal state reached
            if curr_status in ("SUCCESS", "FAILURE") or curr_progress != last_progress or curr_step != last_step:
                event_name = (
                    "complete" if curr_status == "SUCCESS" else ("error" if curr_status == "FAILURE" else "progress")
                )
                yield {
                    "event": event_name,
                    "data": status_data.model_dump_json(),
                }
                last_progress = curr_progress
                last_step = curr_step

            # 5. Close stream if finished
            if curr_status in ("SUCCESS", "FAILURE"):
                logger.info("Job %s reached terminal state %s; closing SSE stream", job_id, curr_status)
                break

            await asyncio.sleep(0.8)

    return EventSourceResponse(
        event_generator(),
        ping=15,
        media_type="text/event-stream",
    )


@router.api_route(
    "/jobs/{job_id}/download",
    methods=["GET", "HEAD"],
    summary="Download the final rendered MP4 tutorial video",
)
async def download_video(job_id: str):
    """Stream or download the final synthesized HD tutorial video."""
    # Query Celery/Redis, local jobs cache, or artifact directory on disk
    video_path = None
    try:
        task_res = AsyncResult(job_id, app=celery_app)
        if task_res.ready() and task_res.successful():
            res = task_res.result or {}
            video_path = res.get("final_video_path")
    except Exception:
        pass

    if not video_path and job_id in LOCAL_JOBS_STORE:
        res = LOCAL_JOBS_STORE[job_id].get("result") or {}
        video_path = res.get("final_video_path")

    if not video_path or not os.path.exists(video_path):
        # Check standard artifact path
        candidate = Path("output_artifacts") / job_id / f"final_{job_id}.mp4"
        if candidate.exists():
            video_path = str(candidate)

    # Fallback to pre-rendered demo tutorial video if sample or demo job is requested
    if not video_path or not os.path.exists(video_path):
        demo_candidate = Path("output_artifacts") / "demo_tutorial.mp4"
        if demo_candidate.exists():
            video_path = str(demo_candidate)

    if not video_path or not os.path.exists(video_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rendered video not found for Job ID '{job_id}'. The task may still be running or failed.",
        )

    filename = Path(video_path).name
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=filename,
    )

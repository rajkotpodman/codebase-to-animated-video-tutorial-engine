"""Celery pipeline tasks for asynchronous tutorial video generation.

Chains together the full open-source codebase-to-video workflow:
  1. Ingestion/Repomix: Clone public GitHub repository and compress codebase structure.
  2. Codebase Graph Mapping: AST-based dependency and topology extraction across components.
  3. Gemini API Script & Scene Generation: Synthesize architecture topology and narration.
  4. Manim Video Rendering: Render animated vector scene to intermediate MP4.
  5. TTS Audio & Subtitles: Synthesize neural voiceover and aligned .srt subtitles.
  6. FFmpeg Final Composition: Scale to HD, sync durations, and burn in subtitles.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from app.workers.celery_worker import celery_app
from app.services.ingestion_service import CodebaseIngestionService, IngestionOptions
from app.services.graph_service import CodebaseGraphService, CodebaseGraph
from app.services.graph_to_manim import generate_manim_flowchart_scene_code
from app.services.gemini_service import GeminiScriptService
from app.services.tts_service import TTSService, TTSOptions
from app.services.video_composer import VideoComposer, VideoComposerOptions
from app.services.storage_service import CloudStorageService
from app.schemas.video_schemas import resolve_language_info
from app.core.sentry import add_sentry_breadcrumb, capture_sentry_exception
from app.core.telemetry import record_job_completion
from manim_engine.base_template import (
    render_architecture_scene,
    scale_manim_script_duration,
    scale_architecture_diagram_duration,
)

logger = logging.getLogger("celery_tasks")


@celery_app.task(bind=True, name="generate_video_pipeline")
def generate_video_pipeline(
    self,
    repo_url: str,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute the end-to-end codebase-to-video generation pipeline.

    Args:
        repo_url: GitHub repository URL or user/repo shorthand
        options: Custom pipeline parameters (voice, resolution, theme, quality)

    Returns:
        Dictionary with final video artifact path, duration, and metadata.
    """
    job_id = self.request.id or f"job_{int(time.time() * 1000)}"
    start_t = time.time()
    try:
        result = run_video_pipeline_sync(
            repo_url=repo_url,
            options=options,
            job_id=job_id,
            task_instance=self,
        )
        record_job_completion("success", time.time() - start_t)
        return result
    except Exception as exc:
        record_job_completion("failure", time.time() - start_t)
        capture_sentry_exception(exc, job_id=job_id, repo_url=repo_url)
        raise


def run_video_pipeline_sync(
    repo_url: str,
    options: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
    task_instance: Optional[Any] = None,
) -> Dict[str, Any]:
    """Synchronous pipeline orchestrator (can be executed inside Celery or standalone)."""
    opts = options or {}
    job_key = job_id or f"local_job_{int(time.time() * 1000)}"
    logger.info("Starting Video Pipeline Execution for Job %s (Repo: %s)", job_key, repo_url)

    # Base workspace for storing job artifacts
    base_artifact_dir = Path(opts.get("artifact_dir", "output_artifacts")) / job_key
    base_artifact_dir.mkdir(parents=True, exist_ok=True)

    def update_progress(step: int, step_name: str, progress: int, message: str) -> None:
        logger.info("[Job %s] Step %d/6 (%s) - %d%%: %s", job_key, step, step_name, progress, message)
        add_sentry_breadcrumb(
            category="pipeline_progress",
            message=f"Step {step}/6 ({step_name}): {message}",
            step=step,
            progress=progress,
            job_id=job_key,
        )
        if task_instance is not None and hasattr(task_instance, "update_state"):
            try:
                task_instance.update_state(
                    state="PROGRESS",
                    meta={
                        "step": step,
                        "step_name": step_name,
                        "progress": progress,
                        "message": message,
                        "job_id": job_key,
                    },
                )
            except Exception as backend_err:
                logger.debug("Could not record intermediate progress in Celery backend: %s", backend_err)

    start_time = time.perf_counter()

    # =========================================================================
    # Step 1: Ingestion & Repomix
    # =========================================================================
    update_progress(1, "Ingestion & Repomix", 15, "Extracting codebase structure...")
    ingest_svc = CodebaseIngestionService(workspace_root=base_artifact_dir / "ingestion")
    ingest_opts = IngestionOptions(
        style="markdown",
        compress=True,
        clone_depth=int(opts.get("clone_depth", 1)),
        branch=opts.get("branch"),
        keep_cloned_repo=True,  # Preserve cloned folder for AST graph extraction
    )

    if os.path.isdir(repo_url):
        ingest_result = ingest_svc.ingest_local_directory(
            directory_path=repo_url,
            options=ingest_opts,
            repo_name=Path(repo_url).name,
        )
    else:
        ingest_result = ingest_svc.ingest_repository(repo_url=repo_url, options=ingest_opts)

    codebase_pack = ingest_result.content
    repo_name = ingest_result.repo_name

    # =========================================================================
    # Step 2: Codebase Graph Mapping (AST & Dependency Analysis)
    # =========================================================================
    update_progress(2, "Codebase Graph Mapping", 25, "Extracting AST dependency graph and architecture nodes...")
    target_repo_dir: Optional[Path] = None
    if ingest_result.cloned_path and Path(ingest_result.cloned_path).is_dir():
        target_repo_dir = Path(ingest_result.cloned_path).resolve()
    elif os.path.isdir(repo_url):
        target_repo_dir = Path(repo_url).resolve()

    max_graph_nodes = int(opts.get("max_graph_nodes", 35))
    graph_svc = CodebaseGraphService(max_nodes=max_graph_nodes)
    codebase_graph: Optional[CodebaseGraph] = None

    if target_repo_dir and target_repo_dir.is_dir():
        try:
            codebase_graph = graph_svc.generate_graph(target_repo_dir, repo_name=repo_name)
            logger.info(
                "CodebaseGraph generated: %d nodes, %d edges for %s",
                len(codebase_graph.nodes),
                len(codebase_graph.edges),
                repo_name,
            )
        except Exception as graph_err:
            logger.warning("CodebaseGraph extraction failed (%s). Continuing with pack.", graph_err)

    # Save intermediate dependency graph artifact
    graph_json_path = base_artifact_dir / "dependency_graph.json"
    if codebase_graph:
        graph_json_path.write_text(codebase_graph.model_dump_json(indent=2), encoding="utf-8")

    # =========================================================================
    # Step 3: AI Script & Scene Synthesis
    # =========================================================================
    update_progress(3, "AI Script & Scene Synthesis", 35, "Synthesizing architecture diagram and narration...")
    target_language = opts.get("target_language", "en")
    gemini_svc = GeminiScriptService(
        api_key=opts.get("gemini_api_key"),
        model=opts.get("gemini_model", "gemini-2.5-flash"),
    )
    synthesis_result = gemini_svc.synthesize_script_and_architecture(
        codebase_pack=codebase_pack,
        repo_name=repo_name,
        custom_instructions=opts.get("custom_instructions"),
        codebase_graph=codebase_graph,
        target_language=target_language,
    )
    architecture_data = synthesis_result.architecture_data
    narration_script = synthesis_result.narration_script
    manim_script = synthesis_result.manim_script

    # Save intermediate planning artifacts
    (base_artifact_dir / "architecture.json").write_text(architecture_data.model_dump_json(indent=2), encoding="utf-8")
    (base_artifact_dir / "narration_script.txt").write_text(narration_script, encoding="utf-8")
    if manim_script:
        (base_artifact_dir / "manim_scene.py").write_text(manim_script, encoding="utf-8")

    # =========================================================================
    # Step 4: TTS Audio Voiceover & Subtitles Synthesis
    # =========================================================================
    update_progress(4, "Audio Voiceover & Subtitles", 50, "Generating neural voiceover and aligning subtitles...")
    tts_svc = TTSService(workspace_dir=base_artifact_dir / "audio")
    tts_opts = TTSOptions(
        voice=opts.get("voice", "en-US-ChristopherNeural"),
        output_format="mp3",
        rate=opts.get("speech_rate", "+0%"),
        language=target_language,
    )
    tts_result = tts_svc.synthesize_script(
        script_text=narration_script,
        options=tts_opts,
    )
    audio_duration = tts_result.duration_seconds
    logger.info(
        "Synthesized voiceover audio (duration=%.2fs, lang=%s, voice=%s)",
        audio_duration,
        target_language,
        tts_result.voice_used,
    )

    # =========================================================================
    # Step 5: Manim Animation Rendering (Dynamically Scaled to Audio Duration)
    # =========================================================================
    update_progress(
        5,
        "Manim Animation Rendering",
        70,
        f"Compiling vector animation scaled to {audio_duration:.1f}s audio duration...",
    )
    manim_quality = opts.get("manim_quality", "l")  # 'l' (480p) for fast preview, 'h' for 1080p
    manim_fps = int(opts.get("fps", 30))
    manim_out_dir = base_artifact_dir / "manim_media"

    # Dynamically scale animation wait times and holds to match exact audio duration, preventing cutoffs & black screens
    if manim_script:
        manim_payload = scale_manim_script_duration(manim_script, target_duration=audio_duration)
    elif codebase_graph:
        manim_payload = generate_manim_flowchart_scene_code(codebase_graph, target_duration=audio_duration)
    else:
        scaled_arch = scale_architecture_diagram_duration(architecture_data, target_duration=audio_duration)
        manim_payload = scaled_arch

    manim_video_path = render_architecture_scene(
        input_data=manim_payload,
        output_dir=manim_out_dir,
        quality=manim_quality,
        fps=manim_fps,
        target_duration=audio_duration,
    )

    # =========================================================================
    # Step 6: FFmpeg Final Composition (pyvideotrans-style sync & anti-black-screen)
    # =========================================================================
    update_progress(
        6, "Final Video Composition", 90, "Merging video, audio, scaling to 1080p, and burning subtitles..."
    )
    composer = VideoComposer()
    composer_opts = VideoComposerOptions(
        target_width=int(opts.get("target_width", 1920)),
        target_height=int(opts.get("target_height", 1080)),
        fps=int(opts.get("fps", 30)),
        burn_subtitles=bool(opts.get("burn_subtitles", True)),
        freeze_last_frame=True,
        pad_audio=True,
        prevent_black_screen=True,
        sync_mode=opts.get("sync_mode", "auto"),
        hold_buffer_sec=float(opts.get("hold_buffer_sec", 0.5)),
    )
    final_output_path = base_artifact_dir / f"final_{job_key}.mp4"
    composition_result = composer.compose_video(
        video_clip=manim_video_path,
        audio_track=tts_result.audio_path,
        subtitle_file=tts_result.srt_path,
        output_path=final_output_path,
        options=composer_opts,
    )

    total_time = time.perf_counter() - start_time
    update_progress(6, "Uploading to Cloud Storage", 96, "Uploading final HD video to cloud storage...")

    # Upload video and subtitles to Cloud Storage (AWS S3 via boto3)
    storage_svc = CloudStorageService()
    storage_res = storage_svc.upload_video_tutorial(
        video_path=composition_result.output_video_path,
        job_id=job_key,
        srt_path=tts_result.srt_path,
    )

    update_progress(6, "Completed", 100, f"Tutorial video successfully rendered in {total_time:.2f}s!")

    # Clean up large intermediate ingestion files if not preserving
    if not opts.get("keep_intermediate_clones", False):
        try:
            ingest_result.cleanup()
            if target_repo_dir and not os.path.isdir(repo_url) and target_repo_dir.exists():
                from app.services.ingestion_service import robust_rmtree
                robust_rmtree(target_repo_dir)
        except Exception as exc:
            logger.debug("Intermediate file cleanup warning: %s", exc)

    return {
        "status": "SUCCESS",
        "job_id": job_key,
        "repo_url": repo_url,
        "repo_name": repo_name,
        "final_video_path": str(composition_result.output_video_path),
        "duration_seconds": round(composition_result.duration_seconds, 2),
        "resolution": f"{composition_result.width}x{composition_result.height}",
        "file_size_bytes": composition_result.file_size_bytes,
        "subtitles_burned": composition_result.has_subtitles,
        "srt_path": str(tts_result.srt_path),
        "audio_path": str(tts_result.audio_path),
        "total_files_packed": ingest_result.total_files,
        "model_used": synthesis_result.model_used,
        "elapsed_seconds": round(total_time, 2),
        "cloud_storage": storage_res,
        "presigned_download_url": storage_res.get("presigned_video_url"),
        "s3_key": storage_res.get("video_key"),
        "storage_provider": storage_res.get("storage_provider"),
        "dependency_graph_path": str(graph_json_path) if graph_json_path.exists() else None,
        "nodes_count": len(codebase_graph.nodes) if codebase_graph else 0,
        "edges_count": len(codebase_graph.edges) if codebase_graph else 0,
        "target_language": target_language,
        "language_name": resolve_language_info(target_language).name,
        "native_language_name": resolve_language_info(target_language).native_name,
    }

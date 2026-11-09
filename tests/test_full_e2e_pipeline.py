"""End-to-End Integration Test Suite for the 5-Stage Video Generation Pipeline.

Validates the full pipeline flow:
  1. Ingestion: Clones mock GitHub repository and packages codebase using Repomix.
  2. Gemini AI Synthesis: Synthesizes architectural topology and narration script.
  3. Manim Animation: Procedurally compiles and renders vector scenes to intermediate MP4.
  4. TTS Audio & Subtitles: Synthesizes neural audio and aligned .srt subtitle cues.
  5. FFmpeg Final Composition: Scales, synchronizes audio/video durations, burns subtitles.
  6. Stream Validation: Verifies that the final MP4 container contains valid H.264/AVC streams.
  7. Celery / Redis Task Queuing: Validates asynchronous execution and task state transitions.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from app.services.gemini_service import GeminiScriptService, ScriptSynthesisResult
from app.services.ingestion_service import CodebaseIngestionService, IngestionOptions
from app.services.storage_service import CloudStorageService
from app.services.tts_service import TTSOptions, TTSService
from app.services.video_composer import VideoComposer, VideoComposerOptions, resolve_ffmpeg_executable
from app.workers.celery_worker import celery_app
from app.workers.tasks import generate_video_pipeline, run_video_pipeline_sync
from manim_engine.base_template import render_architecture_scene
from manim_engine.models import ArchitectureDiagramData

# -----------------------------------------------------------------------------
# Test Credentials & Constants
# -----------------------------------------------------------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "mock_gemini_test_key_for_testing")
TEST_REPO_URL = "https://github.com/mock-org/codevideo-sample-service"


# -----------------------------------------------------------------------------
# Stream Probe & Media Inspection Helper
# -----------------------------------------------------------------------------


def probe_video_streams(file_path: Path | str) -> Dict[str, Any]:
    """Inspects media container streams using FFmpeg and returns stream metadata."""
    ffmpeg_bin = resolve_ffmpeg_executable()
    path = Path(file_path).resolve()
    assert path.exists(), f"Target video file not found at {path}"

    cmd = [ffmpeg_bin, "-hide_banner", "-i", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    output = proc.stderr or proc.stdout

    # Detect H.264 / AVC video codec
    is_h264 = bool(re.search(r"Video:.*(h264|avc1)", output, re.IGNORECASE))
    has_video = bool(re.search(r"Stream.*Video:", output, re.IGNORECASE))
    has_audio = bool(re.search(r"Stream.*Audio:", output, re.IGNORECASE))

    # Parse duration
    duration = 0.0
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if match:
        h, m, s = match.groups()
        duration = int(h) * 3600 + int(m) * 60 + float(s)

    # Parse resolution
    dim_match = re.search(r"Video:.*,\s*(\d{3,4})x(\d{3,4})", output)
    width = int(dim_match.group(1)) if dim_match else 0
    height = int(dim_match.group(2)) if dim_match else 0

    return {
        "is_h264": is_h264,
        "has_video": has_video,
        "has_audio": has_audio,
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "raw_stderr": output,
    }


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_codebase_dir(tmp_path: Path) -> Path:
    """Creates a realistic sample Python microservice repository for ingestion."""
    repo_dir = tmp_path / "sample_service"
    repo_dir.mkdir(parents=True, exist_ok=True)

    (repo_dir / "README.md").write_text(
        "# Payment Gateway Microservice\n"
        "An asynchronous payment processing API built with FastAPI, Redis, and Celery.\n",
        encoding="utf-8",
    )

    (repo_dir / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI(title='Payment Service')\n\n"
        "@app.post('/charge')\n"
        "def charge(amount: int):\n"
        "    return {'status': 'processed', 'amount': amount}\n",
        encoding="utf-8",
    )

    (repo_dir / "database.py").write_text(
        "import sqlite3\n" "def get_connection():\n" "    return sqlite3.connect(':memory:')\n",
        encoding="utf-8",
    )

    return repo_dir


# -----------------------------------------------------------------------------
# Test 1: Stage-by-Stage Isolated Pipeline Verification
# -----------------------------------------------------------------------------


def test_stage_by_stage_pipeline_execution(tmp_path: Path, mock_codebase_dir: Path, mocker: Any):
    """Programmatically executes and validates each of the 5 pipeline stages individually."""
    workspace = tmp_path / "stage_test_workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Stage 1: GitHub Ingestion & Repomix Packing
    # =========================================================================
    ingestion_dir = workspace / "ingestion"
    ingestion_service = CodebaseIngestionService(workspace_root=ingestion_dir)

    # Mock git.Repo.clone_from to copy our local mock codebase safely and instantly
    def fake_clone(url: str, to_path: Path | str, **kwargs: Any) -> MagicMock:
        shutil.copytree(mock_codebase_dir, to_path, dirs_exist_ok=True)
        return MagicMock()

    mocker.patch("git.Repo.clone_from", side_effect=fake_clone)

    ingest_opts = IngestionOptions(style="markdown", compress=True, clone_depth=1)
    ingest_result = ingestion_service.ingest_repository(repo_url=TEST_REPO_URL, options=ingest_opts)

    assert ingest_result.content is not None
    assert len(ingest_result.content) > 100
    assert "Payment Gateway Microservice" in ingest_result.content
    assert ingest_result.total_files >= 3
    assert ingest_result.output_path.exists()
    assert "codevideo-sample-service" in ingest_result.repo_name

    # =========================================================================
    # Stage 2: Gemini API Script & Architecture Data Parsing
    # =========================================================================
    gemini_service = GeminiScriptService(
        api_key=GEMINI_API_KEY,
        model="gemini-3.8-flash",
    )

    synthesis_result: ScriptSynthesisResult = gemini_service.synthesize_script_and_architecture(
        codebase_pack=ingest_result.content,
        repo_name=ingest_result.repo_name,
        custom_instructions="Focus on the payment processing flow and Redis worker queue.",
    )

    assert isinstance(synthesis_result.architecture_data, ArchitectureDiagramData)
    assert len(synthesis_result.architecture_data.nodes) >= 2
    assert synthesis_result.narration_script is not None
    assert len(synthesis_result.narration_script.strip()) > 20
    assert synthesis_result.model_used is not None

    # =========================================================================
    # Stage 3: Manim Vector Animation Scene Rendering
    # =========================================================================
    manim_dir = workspace / "manim_media"
    # Use quality='l' (480p, 15fps) for ultra-fast integration test execution
    manim_mp4_path = render_architecture_scene(
        input_data=synthesis_result.architecture_data,
        output_dir=manim_dir,
        quality="l",
    )

    assert manim_mp4_path.exists()
    assert manim_mp4_path.stat().st_size > 0
    assert manim_mp4_path.suffix.lower() == ".mp4"

    # =========================================================================
    # Stage 4: TTS Neural Audio & SRT Subtitle Synthesis
    # =========================================================================
    audio_dir = workspace / "audio"
    tts_service = TTSService(workspace_dir=audio_dir)
    tts_opts = TTSOptions(voice="en-US-ChristopherNeural", output_format="mp3")

    tts_result = tts_service.synthesize_script(
        script_text=synthesis_result.narration_script,
        options=tts_opts,
    )

    assert tts_result.audio_path.exists()
    assert tts_result.audio_path.stat().st_size > 0
    assert tts_result.srt_path.exists()
    assert tts_result.srt_path.stat().st_size > 0
    assert tts_result.duration_seconds > 0.0

    # Verify SRT format contains valid timestamp lines
    srt_text = tts_result.srt_path.read_text(encoding="utf-8")
    assert "-->" in srt_text, "Generated SRT file missing standard timestamp cue arrows"

    # =========================================================================
    # Stage 5: FFmpeg Final Video Composition & Synchronization
    # =========================================================================
    composer = VideoComposer()
    final_output_path = workspace / "final_stage_test.mp4"
    composer_opts = VideoComposerOptions(
        target_width=640,
        target_height=360,
        fps=15,
        burn_subtitles=True,
        freeze_last_frame=True,
        pad_audio=True,
    )

    composition_result = composer.compose_video(
        video_clip=manim_mp4_path,
        audio_track=tts_result.audio_path,
        subtitle_file=tts_result.srt_path,
        output_path=final_output_path,
        options=composer_opts,
    )

    assert composition_result.output_video_path.exists()
    assert composition_result.output_video_path.stat().st_size > 0
    assert composition_result.duration_seconds > 0.0
    assert composition_result.has_subtitles is True

    # =========================================================================
    # Stage 6: H.264 Stream & Audio Stream Validation
    # =========================================================================
    probe = probe_video_streams(final_output_path)
    assert probe["has_video"] is True, "Output file has no video stream"
    assert probe["is_h264"] is True, f"Output video stream is not H.264/AVC: {probe['raw_stderr']}"
    assert probe["has_audio"] is True, "Output file has no audio stream"
    assert probe["duration_seconds"] > 0.0
    assert probe["width"] == 640
    assert probe["height"] == 360


# -----------------------------------------------------------------------------
# Test 2: Celery Background Task Queuing & Full End-to-End Orchestration
# -----------------------------------------------------------------------------


def test_celery_task_queuing_and_full_pipeline(tmp_path: Path, mock_codebase_dir: Path, mocker: Any):
    """Tests the asynchronous Celery pipeline task queuing and complete execution."""
    # Configure Celery in eager test mode (simulates task queuing and execution in-process)
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        result_backend="cache+memory://",
    )

    # Mock git clone
    def fake_clone(url: str, to_path: Path | str, **kwargs: Any) -> MagicMock:
        shutil.copytree(mock_codebase_dir, to_path, dirs_exist_ok=True)
        return MagicMock()

    mocker.patch("git.Repo.clone_from", side_effect=fake_clone)

    # Mock Cloud Storage upload to return deterministic test presigned URL
    mock_upload = mocker.patch.object(
        CloudStorageService,
        "upload_video_tutorial",
        return_value={
            "presigned_video_url": "https://s3.amazonaws.com/codevideo-tutorials/test_video.mp4",
            "video_key": "tutorials/job_test_e2e_celery/final.mp4",
            "storage_provider": "aws_s3",
            "uploaded": True,
        },
    )

    artifact_dir = tmp_path / "celery_artifacts"
    pipeline_options = {
        "artifact_dir": str(artifact_dir),
        "gemini_api_key": GEMINI_API_KEY,
        "gemini_model": "gemini-3.8-flash",
        "voice": "en-US-ChristopherNeural",
        "manim_quality": "l",
        "target_width": 640,
        "target_height": 360,
        "fps": 15,
        "burn_subtitles": True,
    }

    # Dispatch Celery background task via apply_async
    async_result = generate_video_pipeline.apply_async(
        kwargs={
            "repo_url": TEST_REPO_URL,
            "options": pipeline_options,
        }
    )

    # Verify Celery Task Queuing & Immediate Readiness in Eager Mode
    assert async_result.id is not None
    assert async_result.ready() is True
    assert async_result.state == "SUCCESS"

    result_data = async_result.result
    assert isinstance(result_data, dict)
    assert result_data["status"] == "SUCCESS"
    assert "codevideo-sample-service" in result_data["repo_name"]

    final_video = Path(result_data["final_video_path"])
    assert final_video.exists()
    assert final_video.stat().st_size > 0
    assert result_data["duration_seconds"] > 0
    assert result_data["subtitles_burned"] is True
    assert result_data["presigned_download_url"] == "https://s3.amazonaws.com/codevideo-tutorials/test_video.mp4"

    # Verify cloud upload hook was invoked
    assert mock_upload.called

    # Validate H.264 streams on final video output
    probe = probe_video_streams(final_video)
    assert probe["is_h264"] is True
    assert probe["has_video"] is True
    assert probe["has_audio"] is True

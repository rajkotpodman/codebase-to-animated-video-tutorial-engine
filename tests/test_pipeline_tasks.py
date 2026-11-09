"""End-to-end integration test for the 5-stage video generation pipeline."""

import tempfile
from pathlib import Path
import pytest

from app.workers.tasks import run_video_pipeline_sync


def test_full_video_pipeline_execution():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a local test repository to ingest
        local_repo = Path(tmp_dir) / "test_repo"
        local_repo.mkdir()
        (local_repo / "main.py").write_text(
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n"
            '@app.get("/")\n'
            "def index():\n"
            '    return {"msg": "Hello Pipeline"}\n',
            encoding="utf-8",
        )

        options = {
            "artifact_dir": str(Path(tmp_dir) / "artifacts"),
            "manim_quality": "l",  # 480p for fast test execution
            "target_width": 640,
            "target_height": 360,
            "fps": 15,
            "burn_subtitles": True,
        }

        # Run full pipeline with the local directory as the target repo
        result = run_video_pipeline_sync(
            repo_url=str(local_repo),
            options=options,
            job_id="test_pipeline_job_1",
        )

        assert result["status"] == "SUCCESS"
        assert result["job_id"] == "test_pipeline_job_1"
        assert Path(result["final_video_path"]).exists()
        assert Path(result["final_video_path"]).stat().st_size > 0
        assert Path(result["srt_path"]).exists()
        assert Path(result["audio_path"]).exists()
        assert result["duration_seconds"] > 0
        assert result["total_files_packed"] >= 1

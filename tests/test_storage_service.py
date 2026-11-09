"""Unit tests for CloudStorageService using boto3 SDK and Celery task cloud storage integration."""

import os
from pathlib import Path
import pytest

from app.services.storage_service import CloudStorageConfig, CloudStorageService, UploadResult


def test_storage_service_initialization():
    """Verify CloudStorageService initializes with configuration."""
    config = CloudStorageConfig(
        bucket_name="my-custom-test-bucket",
        region_name="us-west-2",
        presigned_url_expiry_seconds=3600,
    )
    svc = CloudStorageService(config=config)
    assert svc.config.bucket_name == "my-custom-test-bucket"
    assert svc.config.region_name == "us-west-2"
    assert svc.config.presigned_url_expiry_seconds == 3600


def test_storage_service_upload_file(tmp_path: Path):
    """Verify upload_file generates a valid presigned URL and metadata."""
    sample_video = tmp_path / "test_render.mp4"
    sample_video.write_bytes(b"\x00\x00\x00\x20ftypisom" + b"video payload" * 50)

    svc = CloudStorageService()
    result = svc.upload_file(
        local_path=sample_video,
        destination_key="tutorials/job-test-123/video.mp4",
        content_type="video/mp4",
        expiry_seconds=7200,
    )

    assert isinstance(result, UploadResult)
    assert result.key == "tutorials/job-test-123/video.mp4"
    assert result.file_size_bytes == sample_video.stat().st_size
    assert result.content_type == "video/mp4"
    assert "video.mp4" in result.presigned_url
    assert result.expires_in_seconds == 7200


def test_storage_service_upload_video_tutorial(tmp_path: Path):
    """Verify upload_video_tutorial handles both MP4 video and SRT subtitles."""
    video_path = tmp_path / "final_test.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"dummy" * 20)

    srt_path = tmp_path / "subs.srt"
    srt_path.write_text("1\n00:00:01,000 --> 00:00:03,000\nHello World\n", encoding="utf-8")

    svc = CloudStorageService()
    res = svc.upload_video_tutorial(
        video_path=video_path,
        job_id="job_abc_456",
        srt_path=srt_path,
    )

    assert res["video_key"] == "tutorials/job_abc_456/tutorial_job_abc_456.mp4"
    assert "presigned_video_url" in res
    assert res["file_size_bytes"] == video_path.stat().st_size
    assert res["subtitles"] is not None
    assert res["subtitles"]["key"] == "tutorials/job_abc_456/subtitles_job_abc_456.srt"
    assert "presigned_url" in res["subtitles"]


def test_storage_service_nonexistent_file_raises():
    """Verify attempting to upload a missing file raises FileNotFoundError."""
    svc = CloudStorageService()
    with pytest.raises(FileNotFoundError):
        svc.upload_file("nonexistent_path_to_video.mp4")

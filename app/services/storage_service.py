"""Cloud Storage Service integrating AWS S3 (via official boto3 SDK) for video storage and presigned download URLs."""

from __future__ import annotations

import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, Field

logger = logging.getLogger("storage_service")


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------


class CloudStorageConfig(BaseModel):
    """Configuration for S3 or S3-compatible cloud storage."""

    bucket_name: str = Field(default_factory=lambda: os.getenv("AWS_S3_BUCKET", "codevideo-tutorials"))
    region_name: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    aws_access_key_id: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID"))
    aws_secret_access_key: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY"))
    endpoint_url: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_S3_ENDPOINT_URL"))
    presigned_url_expiry_seconds: int = Field(default=86400)  # 24 hours


class UploadResult(BaseModel):
    """Summary of an object uploaded to Cloud Storage."""

    storage_provider: str = "s3"  # "s3" or "local_mock"
    bucket: str
    key: str
    file_size_bytes: int
    content_type: str
    presigned_url: str
    expires_in_seconds: int


# -----------------------------------------------------------------------------
# Cloud Storage Service
# -----------------------------------------------------------------------------


class CloudStorageService:
    """Manages video uploads to AWS S3 / Cloudflare R2 / MinIO and presigned download URL generation."""

    def __init__(self, config: Optional[CloudStorageConfig] = None) -> None:
        self.config = config or CloudStorageConfig()
        self._s3_client = None
        self._is_mock = False

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the boto3 S3 client or fall back to local mock storage in test/offline mode."""
        # Check if AWS credentials or explicit endpoint are present
        has_credentials = bool(self.config.aws_access_key_id and self.config.aws_secret_access_key)
        has_env_credentials = bool(os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE"))

        if not has_credentials and not has_env_credentials and not self.config.endpoint_url:
            logger.info("AWS credentials not detected. Initializing CloudStorageService in development mock mode.")
            self._is_mock = True
            return

        try:
            boto_config = Config(
                region_name=self.config.region_name,
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            )

            client_kwargs: Dict[str, Any] = {"config": boto_config}
            if self.config.aws_access_key_id and self.config.aws_secret_access_key:
                client_kwargs["aws_access_key_id"] = self.config.aws_access_key_id
                client_kwargs["aws_secret_access_key"] = self.config.aws_secret_access_key
            if self.config.endpoint_url:
                client_kwargs["endpoint_url"] = self.config.endpoint_url

            self._s3_client = boto3.client("s3", **client_kwargs)
            logger.info(
                "Boto3 S3 client initialized successfully for bucket '%s' in region '%s'",
                self.config.bucket_name,
                self.config.region_name,
            )
        except Exception as exc:
            logger.warning("Could not initialize boto3 S3 client (%s). Operating in local mock mode.", exc)
            self._is_mock = True

    def upload_file(
        self,
        local_path: str | Path,
        destination_key: Optional[str] = None,
        content_type: Optional[str] = None,
        expiry_seconds: Optional[int] = None,
    ) -> UploadResult:
        """Upload a file to cloud storage and generate a presigned download URL.

        Parameters
        ----------
        local_path : str | Path
            Path to the local file on disk.
        destination_key : str, optional
            Target S3 object key (e.g. 'videos/job-123/final.mp4').
        content_type : str, optional
            MIME type (e.g. 'video/mp4'). Autodetected if None.
        expiry_seconds : int, optional
            Seconds until the presigned URL expires (defaults to 24 hours).
        """
        path = Path(local_path)
        if not path.is_file():
            raise FileNotFoundError(f"Local file to upload not found: {path}")

        file_size = path.stat().st_size
        s3_key = destination_key or f"uploads/{path.name}"
        expiry = expiry_seconds or self.config.presigned_url_expiry_seconds

        # Determine Content-Type
        if not content_type:
            mime, _ = mimetypes.guess_type(str(path))
            content_type = mime or ("video/mp4" if path.suffix == ".mp4" else "application/octet-stream")

        # 1. Local Mock Execution (for unit tests and local dev without AWS credentials)
        if self._is_mock or not self._s3_client:
            simulated_url = (
                f"https://{self.config.bucket_name}.s3.amazonaws.com/{s3_key}?mock_presigned=true&expires={expiry}"
            )
            logger.info("[Mock S3] Simulated upload of %s (size: %d bytes) -> %s", path.name, file_size, s3_key)
            return UploadResult(
                storage_provider="local_mock",
                bucket=self.config.bucket_name,
                key=s3_key,
                file_size_bytes=file_size,
                content_type=content_type,
                presigned_url=simulated_url,
                expires_in_seconds=expiry,
            )

        # 2. Real S3 Upload via boto3
        try:
            extra_args = {
                "ContentType": content_type,
            }
            logger.info(
                "Uploading %s (%d bytes) to s3://%s/%s ...", path.name, file_size, self.config.bucket_name, s3_key
            )
            self._s3_client.upload_file(
                Filename=str(path),
                Bucket=self.config.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args,
            )

            # Generate presigned download URL
            presigned_url = self._s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.config.bucket_name,
                    "Key": s3_key,
                    "ResponseContentType": content_type,
                },
                ExpiresIn=expiry,
            )

            logger.info("S3 upload complete. Presigned URL generated with %d seconds expiry.", expiry)
            return UploadResult(
                storage_provider="s3",
                bucket=self.config.bucket_name,
                key=s3_key,
                file_size_bytes=file_size,
                content_type=content_type,
                presigned_url=presigned_url,
                expires_in_seconds=expiry,
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("S3 upload failed for key '%s': %s", s3_key, exc)
            raise RuntimeError(f"Cloud storage upload error: {exc}") from exc

    def generate_presigned_download_url(self, s3_key: str, expiry_seconds: Optional[int] = None) -> str:
        """Generate a presigned GET URL for an existing S3 object."""
        expiry = expiry_seconds or self.config.presigned_url_expiry_seconds
        if self._is_mock or not self._s3_client:
            return f"https://{self.config.bucket_name}.s3.amazonaws.com/{s3_key}?mock_presigned=true&expires={expiry}"

        try:
            return self._s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.config.bucket_name, "Key": s3_key},
                ExpiresIn=expiry,
            )
        except (BotoCoreError, ClientError) as exc:
            logger.warning("Could not generate presigned URL for %s: %s", s3_key, exc)
            return f"https://{self.config.bucket_name}.s3.amazonaws.com/{s3_key}"

    def upload_video_tutorial(
        self,
        video_path: str | Path,
        job_id: str,
        srt_path: Optional[str | Path] = None,
        expiry_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Convenience method to upload the tutorial MP4 and subtitles to Cloud Storage."""
        video_key = f"tutorials/{job_id}/tutorial_{job_id}.mp4"
        video_upload = self.upload_file(
            local_path=video_path,
            destination_key=video_key,
            content_type="video/mp4",
            expiry_seconds=expiry_seconds,
        )

        subtitles_info = None
        if srt_path and Path(srt_path).is_file():
            try:
                srt_key = f"tutorials/{job_id}/subtitles_{job_id}.srt"
                srt_upload = self.upload_file(
                    local_path=srt_path,
                    destination_key=srt_key,
                    content_type="text/plain; charset=utf-8",
                    expiry_seconds=expiry_seconds,
                )
                subtitles_info = {
                    "key": srt_key,
                    "presigned_url": srt_upload.presigned_url,
                }
            except Exception as e:
                logger.warning("Optional subtitle S3 upload skipped: %s", e)

        return {
            "storage_provider": video_upload.storage_provider,
            "bucket": video_upload.bucket,
            "video_key": video_upload.key,
            "presigned_video_url": video_upload.presigned_url,
            "file_size_bytes": video_upload.file_size_bytes,
            "expires_in_seconds": video_upload.expires_in_seconds,
            "subtitles": subtitles_info,
        }

"""SQLAlchemy database model for video generation jobs and rendering status."""

from __future__ import annotations

import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.models.base import Base


class Job(Base):
    """Video generation task tracking repository, progress, and artifact paths."""

    __tablename__ = "jobs"

    id = Column(String(128), primary_key=True, index=True)
    user_id = Column(String(128), index=True, nullable=True)
    repo_url = Column(String(512), nullable=False)
    status = Column(String(32), default="PENDING", index=True, nullable=False)  # PENDING, PROGRESS, SUCCESS, FAILURE
    progress = Column(Integer, default=0, nullable=False)
    step = Column(Integer, default=1, nullable=False)
    step_name = Column(String(128), default="Queued", nullable=False)
    voice = Column(String(64), default="en-US-ChristopherNeural", nullable=False)
    resolution = Column(String(16), default="1080p", nullable=False)
    theme = Column(String(32), default="midnight", nullable=False)
    video_path = Column(String(512), nullable=True)
    download_url = Column(String(1024), nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} status={self.status} progress={self.progress}%>"

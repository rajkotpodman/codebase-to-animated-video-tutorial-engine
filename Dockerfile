# =============================================================================
# Python Backend & Celery Worker Container
# Supports Manim Community, FFmpeg, GitPython, Repomix CLI, and Edge TTS
# =============================================================================
FROM python:3.11-slim-bookworm AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.cargo/bin:/app/.venv/bin:$PATH"

WORKDIR /app

# -----------------------------------------------------------------------------
# Install System Dependencies:
# - git: For GitPython repository cloning
# - ffmpeg: For video scaling, subtitle burning, and audio padding
# - libcairo2-dev & libpango1.0-dev: Required for Manim Community vector rendering
# - nodejs & npm: Enables Repomix CLI codebase consolidation
# - curl & build-essential: Build utilities and Docker healthcheck
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    git \
    ffmpeg \
    curl \
    libcairo2-dev \
    libpango1.0-dev \
    libffi-dev \
    nodejs \
    npm \
    && npm install -g repomix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Install Python Dependencies
# -----------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Copy Application Source Code
# -----------------------------------------------------------------------------
COPY app/ ./app/
COPY manim_engine/ ./manim_engine/

# Create persistent output directory for media artifacts
RUN mkdir -p /app/output_artifacts && chmod 777 /app/output_artifacts

# Default port for FastAPI
EXPOSE 8000

# Default entrypoint starts the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]


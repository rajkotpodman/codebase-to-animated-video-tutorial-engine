# 📝 Changelog

All notable changes to the **Codebase-to-Animated Video Tutorial Engine** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-09

### 🎉 Initial Production Release

#### Added
* **Autonomous 6-Stage Media Pipeline**:
  * Git repo ingestion with Repomix packaging and structural stripping.
  * Abstract Syntax Tree (AST) code dependency extraction and topological mapping (`graph_service.py` and `graph_to_manim.py`).
  * Gemini 1.5 Flash architectural synthesis generating 4+ distinct animation scenes.
  * Native Microsoft Edge-TTS neural voice synthesis with 21+ languages supported (Hindi, Gujarati, Tamil, Marathi, French, Spanish, German, etc.).
  * Resolution-scaled burned-in subtitle generator (`.srt`).
  * Cairo vector animations powered by the Manim Community library.
  * FFmpeg FastStart broadcast-quality H.264 / AAC MP4 video compositing.
* **Anti-Black Screen & Dynamic Scaling**:
  * Audio synthesis precedes Manim rendering so vector animations dynamically scale to exact narration length.
  * FFmpeg `tpad=stop_mode=clone` filter prevents cutoffs and holds final visual cards until narration completes.
* **Binance Pay Crypto Payments (1 USDT = 1 Video)**:
  * Lossless cropped QR code asset embedded with official Universal QR link: `https://app.binance.com/uni-qr/5HyzYRA1`.
  * Dedicated Binance Pay billing modal tab with real-time payment auto-polling (every 3 seconds).
  * Automated credit fulfillment with official `bizStatus == "PAY_SUCCESS"` webhook listener and idempotent database transactions.
* **Next.js 15 Web Studio**:
  * Dark-themed glassmorphic UI with real-time Server-Sent Events (SSE) progress tracking.
  * Architecture Studio, Video History, API Keys manager, and SaaS billing dashboard.
* **Observability & Health**:
  * Prometheus `/metrics` instrumentation.
  * Official Sentry SDK tracing for FastAPI and Celery.
  * Structured JSON logging via `structlog`.
* **CI/CD Automation**:
  * GitHub Actions workflows for continuous integration, Docker builds, and automated semantic releases.

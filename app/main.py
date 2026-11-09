"""Codebase-to-Animated Video Tutorial Engine - FastAPI Backend.

Provides API routes to trigger automated codebase ingestion, AI script synthesis,
vector animation rendering, neural voiceover generation, and video composition.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.sentry import init_sentry
from app.core.rate_limiter import limiter, rate_limit_custom_handler
from app.core.telemetry import setup_telemetry
from app.core.cache import init_cache
from app.core.logging import setup_logging, StructlogRequestMiddleware, get_logger
from app.api.video_routes import router as video_router
from app.api.billing import router as billing_router
from scalar_fastapi import get_scalar_api_reference

# Initialize structured JSON logging (structlog)
setup_logging(service_name="fastapi-backend")
logger = get_logger("main")

# Initialize official Sentry SDK with FastAPI & Celery integrations
init_sentry(service_name="fastapi-backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize caching and background services."""
    await init_cache(app)
    logger.info("FastAPI application lifecycle startup completed.")
    yield
    logger.info("FastAPI application lifecycle shutdown completed.")


app = FastAPI(
    title="Codebase-to-Animated Video Tutorial Engine",
    description="Automated end-to-end backend service that converts public GitHub codebases into animated tutorial videos.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure SlowAPI Token Bucket rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_custom_handler)
app.add_middleware(SlowAPIMiddleware)

# Request-ID tracking and structured JSON access logging
app.add_middleware(StructlogRequestMiddleware)

# CORS configuration for web dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(video_router)
app.include_router(billing_router)

# Instrument FastAPI with Prometheus metrics at /metrics
setup_telemetry(app)


@app.get("/", tags=["General"])
async def root():
    """Service metadata and health check."""
    return {
        "service": "Codebase-to-Animated Video Tutorial Engine",
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/scalar",
        "endpoints": {
            "scalar_docs": "/scalar",
            "swagger_docs": "/docs",
            "redoc_docs": "/redoc",
            "openapi_spec": "/openapi.json",
            "generate_video": "/api/v1/generate-video",
            "job_status": "/api/v1/jobs/{job_id}",
            "job_stream": "/api/v1/jobs/{job_id}/stream",
            "job_download": "/api/v1/jobs/{job_id}/download",
            "billing": "/api/v1/billing/balance",
            "metrics": "/metrics",
        },
    }


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    """Stunning, modern interactive API documentation powered by Scalar."""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Scalar Interactive API Reference",
        dark_mode=True,
    )


@app.get("/health", tags=["General"])
async def health_check():
    """Liveness probe."""
    return {"status": "healthy"}


@app.get("/sentry-debug", tags=["General"], summary="Trigger test exception for Sentry observability validation")
async def trigger_sentry_error():
    """Triggers an intentional ZeroDivisionError to verify Sentry exception capture."""
    logger.info("Triggering intentional test exception for Sentry error capture...")
    division_by_zero = 1 / 0
    return {"result": division_by_zero}

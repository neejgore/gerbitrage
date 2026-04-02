"""
Wine Pricing Intelligence API – application entrypoint.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import admin, analyze, pricing, search
from app.config import get_settings
from app.services.cache import close_cache, init_cache
from app.services.scheduler import start_scheduler, stop_scheduler

_STATIC_DIR = Path(__file__).parent / "static"

settings = get_settings()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Wine Pricing Intelligence API", version=settings.app_version)
    await init_cache()
    start_scheduler()
    yield
    logger.info("Shutting down…")
    stop_scheduler()
    await close_cache()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Identify wines from menu text, benchmark retail pricing, "
            "estimate wholesale cost, and evaluate restaurant markup fairness."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing middleware ────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed = round((time.monotonic() - start) * 1000)
        response.headers["X-Process-Time-Ms"] = str(elapsed)
        return response

    # ── Health check ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["Meta"], summary="Health check")
    async def health():
        return {"status": "ok", "version": settings.app_version}

    # ── Dashboard ─────────────────────────────────────────────────────────────
    @app.get("/dashboard", tags=["Meta"], summary="Wine Intelligence Dashboard", include_in_schema=False)
    async def dashboard():
        return FileResponse(_STATIC_DIR / "dashboard.html")

    # ── Routers ──────────────────────────────────────────────────────────────
    app.include_router(analyze.router)
    app.include_router(search.router)
    app.include_router(pricing.router)
    app.include_router(admin.router)

    # ── Static files (dashboard assets) ──────────────────────────────────────
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    return app


app = create_app()

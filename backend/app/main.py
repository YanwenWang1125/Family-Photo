"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import ai, albums, auth, media, search
from app.core.config import settings
from app.core.logging import get_logger
from app.workers.ai_worker import shutdown_scheduler, start_scheduler

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting FastAPI application")
    if settings.AI_WORKER_ENABLED:
        start_scheduler()
        logger.info("AI Worker scheduler started")
    else:
        logger.info("AI Worker scheduler is disabled")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application")
    if settings.AI_WORKER_ENABLED:
        shutdown_scheduler()
        logger.info("AI Worker scheduler stopped")


# Create FastAPI application
app = FastAPI(
    title="Family Photo Hub API",
    description="Private, family-only AI-powered photo hub API",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")
app.include_router(albums.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Family Photo Hub API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ai_worker_enabled": settings.AI_WORKER_ENABLED,
    }

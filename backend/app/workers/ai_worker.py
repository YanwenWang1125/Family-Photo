"""
AI Worker with APScheduler for asynchronous media processing.

This module sets up the APScheduler to handle:
- AI tagging of uploaded photos/videos
- Embedding generation for conversational search
- Face detection and clustering
- Batch processing to optimize API costs
"""

import logging
from typing import Any

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Configure job stores and executors
jobstores = {
    "default": MemoryJobStore(),  # Stateless - jobs are recreated on restart
}

executors = {
    "default": AsyncIOExecutor(),
}

job_defaults = {
    "coalesce": True,  # Combine multiple pending executions into one
    "max_instances": 1,  # Only one instance of each job can run at a time
    "misfire_grace_time": 30,  # Seconds after which a missed execution is ignored
}

# Create the scheduler instance
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="UTC",
)


async def process_untagged_media() -> None:
    """
    Process media items that need AI tagging.

    Runs every 2-5 minutes to tag unprocessed media using OpenAI Vision API.
    Processes up to 10 items per run with max 3 concurrent requests.
    """
    from app.workers.tasks.tagging_task import process_untagged_media as process_tagging

    await process_tagging()


async def process_unembedded_media() -> None:
    """
    Generate embeddings for media items that have tags but no embeddings.

    Runs every 5 minutes to create vector embeddings for semantic search.
    Uses batch processing (up to 50 items per API call).
    """
    from app.workers.tasks.embedding_task import (
        process_unembedded_media as process_embeddings,
    )

    await process_embeddings()


async def process_faces() -> None:
    """
    Detect faces in images and cluster them for person identification.

    Runs every 10 minutes (more expensive operation).
    Uses OpenCV for face detection and generates face embeddings.
    """
    logger.info("Starting face detection job")
    try:
        # TODO: Implement when ai_service and db are ready
        # 1. Query media table for images without face detection
        # 2. Download preview images
        # 3. Use OpenCV to detect faces
        # 4. Generate face embeddings
        # 5. Insert into face table
        # 6. Run clustering periodically
        logger.info("Face detection job completed (placeholder)")
    except Exception as e:
        logger.error(
            "Face detection job failed",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )


async def cleanup_failed_jobs() -> None:
    """
    Clean up failed AI processing jobs and reset retry counts.

    Runs daily at 2 AM UTC to maintain database health.
    Resets processing attempts for jobs that have exceeded max retries.
    """
    from app.workers.tasks.cleanup_task import cleanup_failed_jobs as cleanup

    await cleanup()


def setup_scheduler() -> None:
    """
    Configure and add all scheduled jobs to the scheduler.

    This function should be called during application startup.
    Jobs are configured according to the AI Worker implementation guide.
    """
    # Job 1: Process untagged media every 2 minutes
    scheduler.add_job(
        process_untagged_media,
        trigger=IntervalTrigger(seconds=120),  # 2 minutes
        id="ai_tagging",
        name="Process untagged media with AI",
        replace_existing=True,
    )

    # Job 2: Generate embeddings every 5 minutes
    scheduler.add_job(
        process_unembedded_media,
        trigger=IntervalTrigger(seconds=300),  # 5 minutes
        id="ai_embedding",
        name="Generate embeddings for tagged media",
        replace_existing=True,
    )

    # Job 3: Face detection every 10 minutes
    scheduler.add_job(
        process_faces,
        trigger=IntervalTrigger(seconds=600),  # 10 minutes
        id="ai_face_detection",
        name="Detect and cluster faces in images",
        replace_existing=True,
    )

    # Job 4: Cleanup failed jobs daily at 2 AM UTC
    scheduler.add_job(
        cleanup_failed_jobs,
        trigger=CronTrigger(hour=2, minute=0, timezone="UTC"),
        id="ai_cleanup",
        name="Cleanup failed AI processing jobs",
        replace_existing=True,
    )

    logger.info("APScheduler configured with 4 jobs")


def start_scheduler() -> None:
    """
    Start the APScheduler.

    Should be called during FastAPI application startup.
    """
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        logger.info("APScheduler started")
    else:
        logger.warning("APScheduler is already running")


def shutdown_scheduler() -> None:
    """
    Shutdown the APScheduler gracefully.

    Should be called during FastAPI application shutdown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler shut down")
    else:
        logger.warning("APScheduler is not running")


def get_scheduler_status() -> dict[str, Any]:
    """
    Get the current status of the scheduler and jobs.

    Returns:
        Dictionary with scheduler status information.
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
        )

    return {
        "running": scheduler.running,
        "jobs": jobs,
        "job_count": len(jobs),
    }

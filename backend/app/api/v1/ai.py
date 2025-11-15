"""AI processing endpoints for monitoring and management."""

from fastapi import APIRouter

from app.core.logging import get_logger
from app.workers.ai_worker import get_scheduler_status, scheduler
from app.workers.monitoring import get_last_successful_run, get_pending_count

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health")
async def ai_worker_health() -> dict:
    """
    Health check endpoint for AI worker.

    Returns:
        dict: Scheduler status, pending jobs, and last run information
    """
    try:
        # Get scheduler status
        scheduler_status = get_scheduler_status()

        # Get pending job counts
        pending = await get_pending_count()

        # Get last successful run information
        last_run = await get_last_successful_run()

        return {
            "scheduler_running": scheduler_status["running"],
            "jobs": scheduler_status["jobs"],
            "pending_jobs": pending,
            "last_run": last_run,
            "status": "healthy" if scheduler_status["running"] else "stopped",
        }
    except Exception as e:
        logger.error(
            "Error getting AI worker health",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        return {
            "scheduler_running": False,
            "jobs": [],
            "pending_jobs": {"total": 0},
            "last_run": {},
            "status": "error",
            "error": str(e),
        }

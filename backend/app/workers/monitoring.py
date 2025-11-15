"""Monitoring utilities for AI Worker status and metrics."""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.media import Media
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)


async def get_pending_count() -> dict[str, int]:
    """
    Get count of pending AI processing jobs.

    Returns:
        dict: Counts of pending jobs by type
    """
    try:
        async with AsyncSessionLocal() as db:
            # Count unprocessed media (tagging pending)
            untagged_stmt = select(func.count(Media.id)).where(
                Media.ai_processed == False,  # noqa: E712
                Media.ai_processing_attempts < 3,
                Media.preview_blob_path.isnot(None),
            )
            untagged_result = await db.execute(untagged_stmt)
            untagged_count = untagged_result.scalar() or 0

            # Count unembedded media (embedding pending)
            unembedded_stmt = select(func.count(Media.id)).where(
                Media.embedding.is_(None),
                Media.ai_processed == True,  # noqa: E712
            )
            unembedded_result = await db.execute(unembedded_stmt)
            unembedded_count = unembedded_result.scalar() or 0

            # Count failed jobs
            failed_stmt = select(func.count(Media.id)).where(
                Media.ai_processing_attempts >= 3
            )
            failed_result = await db.execute(failed_stmt)
            failed_count = failed_result.scalar() or 0

            return {
                "untagged": untagged_count,
                "unembedded": unembedded_count,
                "failed": failed_count,
                "total": untagged_count + unembedded_count,
            }
    except Exception as e:
        logger.error(
            "Failed to get pending count",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        return {
            "untagged": 0,
            "unembedded": 0,
            "failed": 0,
            "total": 0,
        }


async def get_last_successful_run() -> dict[str, Any]:
    """
    Get information about the last successful AI processing runs.

    Returns:
        dict: Last successful run timestamps and counts
    """
    try:
        async with AsyncSessionLocal() as db:
            # Get most recently processed media
            last_tagged_stmt = (
                select(func.max(Media.last_ai_attempt_at))
                .where(Media.ai_processed == True)  # noqa: E712
            )
            last_tagged_result = await db.execute(last_tagged_stmt)
            last_tagged = last_tagged_result.scalar()

            # Get most recently embedded media
            last_embedded_stmt = (
                select(func.max(Media.upload_date))
                .where(Media.embedding.isnot(None))
            )
            last_embedded_result = await db.execute(last_embedded_stmt)
            last_embedded = last_embedded_result.scalar()

            # Count processed today
            today = datetime.utcnow().date()
            processed_today_stmt = select(func.count(Media.id)).where(
                Media.ai_processed == True,  # noqa: E712
                func.date(Media.last_ai_attempt_at) == today,
            )
            processed_today_result = await db.execute(processed_today_stmt)
            processed_today = processed_today_result.scalar() or 0

            return {
                "last_tagged": last_tagged.isoformat() if last_tagged else None,
                "last_embedded": last_embedded.isoformat() if last_embedded else None,
                "processed_today": processed_today,
            }
    except Exception as e:
        logger.error(
            "Failed to get last successful run",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        return {
            "last_tagged": None,
            "last_embedded": None,
            "processed_today": 0,
        }


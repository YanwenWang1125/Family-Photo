"""Cleanup task for maintaining database health by handling failed AI processing jobs."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models.media import Media
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)


async def cleanup_failed_jobs() -> None:
    """
    Clean up failed AI processing jobs and reset retry counts.

    Runs daily at 2 AM UTC to maintain database health.
    Logs summary of failed items and optionally resets attempts for old failures.
    """
    if not settings.AI_WORKER_ENABLED:
        logger.debug("AI worker is disabled, skipping cleanup job")
        return

    logger.info("Starting cleanup of failed jobs")

    try:
        async with AsyncSessionLocal() as db:
            # Find media with ai_processing_attempts >= max retry attempts
            stmt = select(Media).where(
                Media.ai_processing_attempts >= settings.AI_MAX_RETRY_ATTEMPTS
            )
            result = await db.execute(stmt)
            failed_media = list(result.scalars().all())

            if not failed_media:
                logger.info("No failed jobs found to clean up")
                return

            # Count by status
            total_failed = len(failed_media)
            processed_failed = sum(1 for m in failed_media if m.ai_processed)
            unprocessed_failed = total_failed - processed_failed

            # Log summary
            logger.info(
                "Found failed AI processing jobs",
                extra={
                    "total_failed": total_failed,
                    "processed_failed": processed_failed,
                    "unprocessed_failed": unprocessed_failed,
                },
            )

            # Optionally reset attempts for old failures (older than 7 days)
            # This allows retrying after some time has passed
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            reset_count = 0

            for media in failed_media:
                # Only reset if last attempt was more than 7 days ago
                if (
                    media.last_ai_attempt_at
                    and media.last_ai_attempt_at < cutoff_date
                ):
                    media.ai_processing_attempts = 0
                    reset_count += 1
                    logger.debug(
                        f"Reset processing attempts for media {media.id}",
                        extra={
                            "media_id": str(media.id),
                            "last_attempt": media.last_ai_attempt_at.isoformat(),
                        },
                    )

            if reset_count > 0:
                await db.commit()
                logger.info(
                    f"Reset processing attempts for {reset_count} old failed jobs",
                    extra={"reset_count": reset_count},
                )
            else:
                logger.info("No old failed jobs to reset")

            # Log detailed summary
            logger.info(
                "Cleanup job completed",
                extra={
                    "total_failed": total_failed,
                    "processed_failed": processed_failed,
                    "unprocessed_failed": unprocessed_failed,
                    "reset_count": reset_count,
                },
            )

    except Exception as e:
        logger.error(
            "Cleanup job failed",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )


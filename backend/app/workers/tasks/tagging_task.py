"""Tagging task for AI-powered media tagging using OpenAI Vision API."""

import asyncio
from datetime import datetime
from typing import Optional

from openai import RateLimitError as OpenAIRateLimitError
from openai import APIError as OpenAIAPIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models.media import Media
from app.db.models.tag import Tag
from app.db.session import AsyncSessionLocal
from app.services.ai_service import process_media_tagging
from app.utils.azure_blob import download_blob, generate_sas_url

logger = get_logger(__name__)


async def get_unprocessed_media(
    db: AsyncSession,
    batch_size: int = 10,
) -> list[Media]:
    """
    Get media items that need AI processing.

    Args:
        db: Database session
        batch_size: Maximum number of items to return

    Returns:
        list[Media]: List of unprocessed media items
    """
    stmt = (
        select(Media)
        .where(Media.ai_processed == False)  # noqa: E712
        .where(Media.ai_processing_attempts < settings.AI_MAX_RETRY_ATTEMPTS)
        .where(Media.preview_blob_path.isnot(None))
        .where(Media.mime_type.like("image/%"))  # Only process images for now
        .order_by(Media.upload_date.desc())
        .limit(batch_size)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def process_single_media(
    media: Media,
    db: AsyncSession,
    correlation_id: Optional[str] = None,
) -> bool:
    """
    Process a single media item for AI tagging.

    Args:
        media: Media object to process
        db: Database session
        correlation_id: Optional correlation ID for logging

    Returns:
        bool: True if successful, False otherwise
    """
    media_id_str = str(media.id)
    log_extra = {
        "media_id": media_id_str,
        "correlation_id": correlation_id or media_id_str,
    }

    try:
        # Update attempt timestamp
        media.last_ai_attempt_at = datetime.utcnow()
        media.ai_processing_attempts += 1
        await db.flush()

        # Generate SAS URL for preview image (15 min expiry)
        if not media.preview_blob_path:
            logger.warning(
                "Media has no preview_blob_path, skipping",
                extra=log_extra,
            )
            return False

        try:
            image_url = await generate_sas_url(
                container_name=settings.AZURE_BLOB_CONTAINER_PREVIEW,
                blob_path=media.preview_blob_path,
                expiry_minutes=15,
                read_only=True,
            )
        except Exception as e:
            logger.error(
                "Failed to generate SAS URL for preview",
                extra={
                    **log_extra,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            return False

        # Call OpenAI Vision API
        try:
            ai_result = await process_media_tagging(
                image_url=image_url,
                media_id=media_id_str,
            )
        except OpenAIRateLimitError as e:
            logger.warning(
                "OpenAI rate limit exceeded, will retry later",
                extra=log_extra,
            )
            # Don't increment attempts for rate limits - will retry
            media.ai_processing_attempts -= 1
            await db.flush()
            return False
        except OpenAIAPIError as e:
            logger.error(
                "OpenAI API error during tagging",
                extra={
                    **log_extra,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "attempt": media.ai_processing_attempts,
                },
                exc_info=True,
            )
            # Attempts already incremented, will retry if under limit
            return False

        # Extract tags
        tags = ai_result.get("tags", [])
        if not tags:
            logger.warning(
                "No tags returned from AI",
                extra=log_extra,
            )
            # Mark as processed even if no tags (to avoid infinite retries)
            media.ai_processed = True
            media.ai_tags = ai_result.get("raw_response", {})
            await db.commit()
            return True

        # Save tags to database
        for tag_name in tags:
            if not tag_name or not isinstance(tag_name, str):
                continue

            # Check if tag already exists for this media
            existing_tag = await db.execute(
                select(Tag).where(
                    Tag.media_id == media.id,
                    Tag.tag_name == tag_name,
                    Tag.source == "ai",
                )
            )
            if existing_tag.scalar_one_or_none():
                continue  # Skip duplicate tags

            # Create new tag
            tag = Tag(
                media_id=media.id,
                tag_name=tag_name.strip(),
                source="ai",
                confidence=None,  # OpenAI Vision doesn't provide confidence scores
            )
            db.add(tag)

        # Update media record
        media.ai_processed = True
        media.ai_tags = ai_result.get("raw_response", {})
        media.ai_processing_attempts = 0  # Reset on success

        await db.commit()

        logger.info(
            "AI tagging completed successfully",
            extra={
                **log_extra,
                "tags_count": len(tags),
                "processing_time_ms": None,  # Could add timing if needed
            },
        )

        return True

    except Exception as e:
        logger.error(
            "Unexpected error processing media",
            extra={
                **log_extra,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "attempt": media.ai_processing_attempts,
            },
            exc_info=True,
        )
        await db.rollback()
        return False


async def process_media_batch(
    media_list: list[Media],
    db: AsyncSession,
    max_concurrent: int = 3,
) -> dict[str, int]:
    """
    Process a batch of media items with concurrency control.

    Args:
        media_list: List of media items to process
        db: Database session
        max_concurrent: Maximum concurrent API calls

    Returns:
        dict: Statistics with 'success', 'failed', 'total' counts
    """
    if not media_list:
        return {"success": 0, "failed": 0, "total": 0}

    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(media: Media) -> bool:
        async with semaphore:
            # Create a new session for each media item to avoid conflicts
            async with AsyncSessionLocal() as item_db:
                try:
                    # Refresh media object in new session
                    media_refreshed = await item_db.get(Media, media.id)
                    if not media_refreshed:
                        return False
                    return await process_single_media(media_refreshed, item_db)
                except Exception as e:
                    logger.error(
                        f"Error in semaphore-controlled processing: {e}",
                        extra={"media_id": str(media.id)},
                        exc_info=True,
                    )
                    return False

    # Process all media items with concurrency control
    tasks = [process_with_semaphore(media) for media in media_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successes and failures
    success_count = sum(1 for r in results if r is True)
    failed_count = len(results) - success_count

    stats = {
        "success": success_count,
        "failed": failed_count,
        "total": len(media_list),
    }

    logger.info(
        "Batch processing completed",
        extra=stats,
    )

    return stats


async def process_untagged_media() -> None:
    """
    Main function to process all untagged media items.

    This function is called by the APScheduler job.
    Queries for unprocessed media, processes them in batches with concurrency control.
    """
    if not settings.AI_WORKER_ENABLED:
        logger.debug("AI worker is disabled, skipping tagging job")
        return

    logger.info("Starting AI tagging job")

    try:
        async with AsyncSessionLocal() as db:
            # Get unprocessed media
            unprocessed = await get_unprocessed_media(
                db=db,
                batch_size=settings.AI_BATCH_SIZE,
            )

            if not unprocessed:
                logger.debug("No unprocessed media found")
                return

            logger.info(
                f"Found {len(unprocessed)} unprocessed media items",
                extra={"batch_size": len(unprocessed)},
            )

            # Process batch with concurrency control
            stats = await process_media_batch(
                media_list=unprocessed,
                db=db,
                max_concurrent=settings.AI_MAX_CONCURRENT_REQUESTS,
            )

            logger.info(
                "AI tagging job completed",
                extra=stats,
            )

    except Exception as e:
        logger.error(
            "AI tagging job failed",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )


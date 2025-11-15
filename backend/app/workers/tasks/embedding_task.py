"""Embedding task for generating vector embeddings for semantic search."""

from typing import Optional

from openai import APIError as OpenAIAPIError
from openai import RateLimitError as OpenAIRateLimitError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models.media import Media
from app.db.session import AsyncSessionLocal
from app.services.ai_service import generate_embeddings_batch

logger = get_logger(__name__)


def create_tag_text(media: Media) -> Optional[str]:
    """
    Create a text description from media tags for embedding generation.

    Args:
        media: Media object with loaded tags

    Returns:
        str: Comma-separated tag names, or None if no tags
    """
    if not media.tags:
        return None

    # Extract tag names and join with commas
    tag_names = [tag.tag_name for tag in media.tags if tag.tag_name]
    if not tag_names:
        return None

    # Join tags with comma and space
    return ", ".join(tag_names)


async def get_unembedded_media(
    db: AsyncSession,
    batch_size: int = 50,
) -> list[Media]:
    """
    Get media items that have tags but no embeddings.

    Args:
        db: Database session
        batch_size: Maximum number of items to return (max 50 for OpenAI batch API)

    Returns:
        list[Media]: List of media items with tags but no embeddings
    """
    # Query media with tags but no embedding
    # Use selectinload to eagerly load tags relationship
    stmt = (
        select(Media)
        .where(Media.embedding.is_(None))
        .where(Media.ai_processed == True)  # noqa: E712 - Only process media that has been tagged
        .options(selectinload(Media.tags))
        .order_by(Media.upload_date.desc())
        .limit(batch_size)
    )

    result = await db.execute(stmt)
    media_list = list(result.scalars().unique().all())

    # Filter to only include media that actually has tags
    media_with_tags = []
    for media in media_list:
        # Ensure tags are loaded
        if not media.tags:
            # Try to load tags if not already loaded
            await db.refresh(media, ["tags"])
        if media.tags:
            media_with_tags.append(media)

    return media_with_tags


async def process_embedding_batch(
    media_list: list[Media],
    db: AsyncSession,
) -> dict[str, int]:
    """
    Process a batch of media items to generate embeddings.

    Args:
        media_list: List of media items to process
        db: Database session

    Returns:
        dict: Statistics with 'success', 'failed', 'total' counts
    """
    if not media_list:
        return {"success": 0, "failed": 0, "total": 0}

    # Create text descriptions from tags
    media_text_pairs: list[tuple[Media, str]] = []
    for media in media_list:
        tag_text = create_tag_text(media)
        if tag_text:
            media_text_pairs.append((media, tag_text))
        else:
            logger.warning(
                f"Media {media.id} has no tags, skipping embedding generation",
                extra={"media_id": str(media.id)},
            )

    if not media_text_pairs:
        logger.info("No media with tags found in batch")
        return {"success": 0, "failed": 0, "total": len(media_list)}

    # Extract texts for batch API call
    texts = [text for _, text in media_text_pairs]
    media_items = [media for media, _ in media_text_pairs]

    # Generate embeddings in batch
    try:
        embeddings = await generate_embeddings_batch(texts)
    except OpenAIRateLimitError as e:
        logger.warning(
            "OpenAI rate limit exceeded for embeddings, will retry later",
            extra={"batch_size": len(texts)},
        )
        return {"success": 0, "failed": len(media_items), "total": len(media_list)}
    except OpenAIAPIError as e:
        logger.error(
            "OpenAI API error during batch embedding generation",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "batch_size": len(texts),
            },
            exc_info=True,
        )
        return {"success": 0, "failed": len(media_items), "total": len(media_list)}

    # Verify we got the expected number of embeddings
    if len(embeddings) != len(media_items):
        logger.error(
            f"Mismatch between embeddings ({len(embeddings)}) and media items ({len(media_items)})",
            extra={
                "embeddings_count": len(embeddings),
                "media_count": len(media_items),
            },
        )
        return {"success": 0, "failed": len(media_items), "total": len(media_list)}

    # Update media records with embeddings
    success_count = 0
    failed_count = 0

    for media, embedding in zip(media_items, embeddings):
        try:
            # Verify embedding dimensions (should be 1536 for text-embedding-3-small)
            if len(embedding) != 1536:
                logger.warning(
                    f"Unexpected embedding dimensions: {len(embedding)} (expected 1536)",
                    extra={"media_id": str(media.id)},
                )

            # Store embedding
            media.embedding = embedding
            await db.flush()

            success_count += 1

            logger.debug(
                "Embedding generated and stored",
                extra={
                    "media_id": str(media.id),
                    "embedding_dimensions": len(embedding),
                    "tag_count": len(media.tags),
                },
            )

        except Exception as e:
            failed_count += 1
            logger.error(
                "Failed to store embedding",
                extra={
                    "media_id": str(media.id),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

    # Commit all successful updates
    try:
        await db.commit()
        logger.info(
            "Batch embedding generation completed",
            extra={
                "success": success_count,
                "failed": failed_count,
                "total": len(media_list),
            },
        )
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to commit embedding updates",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        return {"success": 0, "failed": len(media_items), "total": len(media_list)}

    return {
        "success": success_count,
        "failed": failed_count,
        "total": len(media_list),
    }


async def process_unembedded_media() -> None:
    """
    Main function to process all media items that need embeddings.

    This function is called by the APScheduler job.
    Queries for media with tags but no embeddings, processes them in batches.
    """
    if not settings.AI_WORKER_ENABLED:
        logger.debug("AI worker is disabled, skipping embedding job")
        return

    logger.info("Starting embedding generation job")

    try:
        async with AsyncSessionLocal() as db:
            # Get unembedded media (max 50 for OpenAI batch API)
            unembedded = await get_unembedded_media(
                db=db,
                batch_size=50,  # OpenAI batch API limit
            )

            if not unembedded:
                logger.debug("No unembedded media found")
                return

            logger.info(
                f"Found {len(unembedded)} media items needing embeddings",
                extra={"batch_size": len(unembedded)},
            )

            # Process batch
            stats = await process_embedding_batch(
                media_list=unembedded,
                db=db,
            )

            logger.info(
                "Embedding generation job completed",
                extra=stats,
            )

    except Exception as e:
        logger.error(
            "Embedding generation job failed",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )


"""AI service for OpenAI Vision API and Embeddings."""

import base64
import json
import logging
from typing import Any, Optional

from openai import AsyncOpenAI
from openai import RateLimitError as OpenAIRateLimitError
from openai import APIError as OpenAIAPIError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client
_openai_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    """
    Get or create the OpenAI client.

    Returns:
        AsyncOpenAI: OpenAI async client
    """
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


async def process_media_tagging(
    image_url: str,
    media_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Call OpenAI Vision API to analyze an image and extract descriptive tags.

    Args:
        image_url: URL to the image (can be blob URL with SAS token or base64)
        media_id: Optional media ID for logging correlation

    Returns:
        dict: Contains 'tags' (list of tag strings) and 'raw_response' (full AI response)

    Raises:
        OpenAIRateLimitError: When rate limit is exceeded
        OpenAIAPIError: For other OpenAI API errors
    """
    client = get_openai_client()

    prompt = (
        "Analyze this image and provide descriptive tags. "
        "Return a JSON object with the following structure: "
        '{"tags": ["tag1", "tag2", ...], "objects": [...], "scene": "...", '
        '"mood": "...", "activities": [...], "colors": [...], "time_of_day": "..."}. '
        "Be concise and specific. Focus on what is visible in the image."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI Vision API")

        # Parse JSON response
        try:
            parsed_response = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse OpenAI response as JSON: {content}",
                extra={"media_id": media_id},
                exc_info=True,
            )
            # Fallback: try to extract tags from text
            parsed_response = {"tags": content.split(", ") if content else []}

        # Extract tags list (primary field)
        tags = parsed_response.get("tags", [])
        if not isinstance(tags, list):
            # If tags is not a list, try to extract from other fields
            tags = []
            for key in ["objects", "activities", "colors"]:
                if key in parsed_response and isinstance(parsed_response[key], list):
                    tags.extend(parsed_response[key])

        result = {
            "tags": tags if tags else [],
            "raw_response": parsed_response,
        }

        logger.info(
            "AI tagging completed",
            extra={
                "media_id": media_id,
                "tags_count": len(result["tags"]),
                "model": settings.OPENAI_VISION_MODEL,
            },
        )

        return result

    except OpenAIRateLimitError as e:
        logger.warning(
            "OpenAI rate limit exceeded",
            extra={"media_id": media_id},
            exc_info=True,
        )
        raise
    except OpenAIAPIError as e:
        logger.error(
            "OpenAI API error",
            extra={
                "media_id": media_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in AI tagging",
            extra={
                "media_id": media_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        raise


async def generate_embedding(text: str) -> list[float]:
    """
    Generate embedding from text using OpenAI Embeddings API.

    Args:
        text: Text to generate embedding for

    Returns:
        list[float]: Embedding vector (1536 dimensions for text-embedding-3-small)

    Raises:
        OpenAIAPIError: For OpenAI API errors
    """
    client = get_openai_client()

    try:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
        )

        embedding = response.data[0].embedding
        logger.debug(
            f"Generated embedding: {len(embedding)} dimensions",
            extra={"text_length": len(text)},
        )

        return embedding

    except OpenAIAPIError as e:
        logger.error(
            "OpenAI embedding API error",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        raise


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in one API call (batch processing).

    Args:
        texts: List of texts to generate embeddings for (max 50)

    Returns:
        list[list[float]]: List of embedding vectors

    Raises:
        ValueError: If more than 50 texts provided
        OpenAIAPIError: For OpenAI API errors
    """
    if len(texts) > 50:
        raise ValueError("OpenAI Embeddings API supports max 50 texts per batch")

    client = get_openai_client()

    try:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=texts,
        )

        embeddings = [data.embedding for data in response.data]
        logger.debug(
            f"Generated {len(embeddings)} embeddings in batch",
            extra={"batch_size": len(texts)},
        )

        return embeddings

    except OpenAIAPIError as e:
        logger.error(
            "OpenAI batch embedding API error",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "batch_size": len(texts),
            },
            exc_info=True,
        )
        raise

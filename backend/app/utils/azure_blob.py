"""Azure Blob Storage utilities for media storage and retrieval."""

import asyncio
import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global blob service client (lazy initialization)
_blob_service_client: Optional[BlobServiceClient] = None


def get_blob_service_client() -> BlobServiceClient:
    """
    Get or create the Azure Blob Service Client.

    Returns:
        BlobServiceClient: Async Azure Blob Service Client
    """
    global _blob_service_client
    if _blob_service_client is None:
        _blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_BLOB_CONNECTION_STRING
        )
    return _blob_service_client


async def download_blob(container_name: str, blob_path: str) -> bytes:
    """
    Download a blob from Azure Blob Storage.

    Args:
        container_name: Name of the container
        blob_path: Path to the blob within the container

    Returns:
        bytes: Blob content as bytes

    Raises:
        ResourceNotFoundError: If blob or container doesn't exist
        Exception: For other Azure storage errors
    """
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_path)

    try:
        download_stream = await blob_client.download_blob()
        content = await download_stream.readall()
        logger.debug(
            f"Downloaded blob: {container_name}/{blob_path} ({len(content)} bytes)"
        )
        return content
    except ResourceNotFoundError as e:
        logger.error(
            f"Blob not found: {container_name}/{blob_path}",
            extra={"container": container_name, "blob_path": blob_path},
        )
        raise
    except Exception as e:
        logger.error(
            f"Error downloading blob: {container_name}/{blob_path}",
            extra={
                "container": container_name,
                "blob_path": blob_path,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def generate_sas_url(
    container_name: str,
    blob_path: str,
    expiry_minutes: int = 15,
    read_only: bool = True,
) -> str:
    """
    Generate a short-lived SAS URL for blob access.

    Args:
        container_name: Name of the container
        blob_path: Path to the blob within the container
        expiry_minutes: Minutes until SAS token expires (default: 15)
        read_only: If True, generate read-only SAS (default: True)

    Returns:
        str: SAS URL for the blob
    """
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_path)

    # Generate SAS token using the blob client
    # This works with connection string authentication
    from azure.storage.blob import BlobSasPermissions, generate_blob_sas

    # Extract account name and key from connection string
    # Connection string format: "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=..."
    conn_str = settings.AZURE_BLOB_CONNECTION_STRING
    account_name = None
    account_key = None

    for part in conn_str.split(";"):
        if part.startswith("AccountName="):
            account_name = part.split("=", 1)[1]
        elif part.startswith("AccountKey="):
            account_key = part.split("=", 1)[1]

    if not account_name or not account_key:
        raise ValueError(
            "Could not extract account name or key from connection string"
        )

    # Generate SAS token
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_path,
        account_key=account_key,
        permission=BlobSasPermissions(read=True)
        if read_only
        else BlobSasPermissions(read=True, write=True),
        expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )

    # Construct SAS URL
    blob_url = blob_client.url
    sas_url = f"{blob_url}?{sas_token}"

    return sas_url


async def upload_to_blob(
    container_name: str,
    blob_path: str,
    data: bytes,
    content_type: Optional[str] = None,
) -> str:
    """
    Upload data to Azure Blob Storage.

    Args:
        container_name: Name of the container
        blob_path: Path to the blob within the container
        data: Data to upload as bytes
        content_type: MIME type of the content (optional)

    Returns:
        str: Blob URL
    """
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_path)

    # Upload blob
    await blob_client.upload_blob(
        data,
        overwrite=True,
        content_settings={"content_type": content_type} if content_type else None,
    )

    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_path}"
    logger.debug(f"Uploaded blob: {blob_url} ({len(data)} bytes)")
    return blob_url


async def delete_from_blob(container_name: str, blob_path: str) -> None:
    """
    Delete a blob from Azure Blob Storage.

    Args:
        container_name: Name of the container
        blob_path: Path to the blob within the container
    """
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_path)

    await blob_client.delete_blob()
    logger.debug(f"Deleted blob: {container_name}/{blob_path}")


async def close_blob_service_client() -> None:
    """Close the blob service client connection."""
    global _blob_service_client
    if _blob_service_client is not None:
        await _blob_service_client.close()
        _blob_service_client = None

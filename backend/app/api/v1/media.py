"""Media endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/media", tags=["media"])

# TODO: Implement media upload, retrieval, deletion, and SAS token generation

"""Authentication endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# TODO: Implement JWT authentication, login, refresh token, and logout endpoints

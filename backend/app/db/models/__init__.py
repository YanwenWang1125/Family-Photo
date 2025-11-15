"""Database models package - exports all models for Alembic autogenerate."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Import all models here for Alembic autogenerate
from app.db.models.media import Media  # noqa: E402
from app.db.models.tag import Tag  # noqa: E402

__all__ = ["Base", "Media", "Tag"]

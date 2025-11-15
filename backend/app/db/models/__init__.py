"""Database models package - exports all models for Alembic autogenerate."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


# Import all models here for Alembic autogenerate
from app.db.models.user import User  # noqa: E402
from app.db.models.media import Media  # noqa: E402
from app.db.models.album import Album, album_media  # noqa: E402
from app.db.models.tag import Tag  # noqa: E402
from app.db.models.face import Face  # noqa: E402

__all__ = ["Base", "UUIDMixin", "TimestampMixin", "User", "Media", "Album", "album_media", "Tag", "Face"]

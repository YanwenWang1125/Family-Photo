"""Album model for photo albums/collections."""

from typing import Optional

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import Base, UUIDMixin, TimestampMixin


# Association table for many-to-many relationship
album_media = Table(
    "album_media",
    Base.metadata,
    Column(
        "album_id",
        UUID(as_uuid=True),
        ForeignKey("album.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "media_id",
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Album(Base, UUIDMixin, TimestampMixin):
    """Photo album/collection."""

    __tablename__ = "album"

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Cover image (optional)
    cover_media_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Creator
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="albums",
    )
    media_items: Mapped[list["Media"]] = relationship(
        "Media",
        secondary=album_media,
        back_populates="albums",
    )

    def __repr__(self) -> str:
        return f"<Album {self.name}>"

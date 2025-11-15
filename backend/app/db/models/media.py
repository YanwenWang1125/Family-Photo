"""Media model for storing photo and video metadata."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.models import Base, UUIDMixin, TimestampMixin


class Media(Base, UUIDMixin, TimestampMixin):
    """Photo or video media item."""

    __tablename__ = "media"

    # Basic metadata
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,  # For filtering by type
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Blob storage paths
    original_blob_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    preview_blob_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Image/Video properties
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Duration in seconds for videos",
    )

    # Upload metadata
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,  # For timeline queries
    )
    taken_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,  # For sorting by photo date
        comment="Date photo/video was taken (from EXIF)",
    )

    # AI processing state
    ai_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,  # For worker queries
    )
    ai_processing_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    ai_tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Raw AI response with tags, objects, scene, etc.",
    )
    last_ai_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Embeddings for semantic search (1536 dimensions for text-embedding-3-small)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(1536),
        nullable=True,
    )

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="media")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="media",
        cascade="all, delete-orphan",
    )
    faces: Mapped[list["Face"]] = relationship(
        "Face",
        back_populates="media",
        cascade="all, delete-orphan",
    )
    albums: Mapped[list["Album"]] = relationship(
        "Album",
        secondary="album_media",
        back_populates="media_items",
    )

    def __repr__(self) -> str:
        return f"<Media {self.filename} ({self.mime_type})>"
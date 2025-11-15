"""Media model for storing photo and video metadata."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Float, JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import AsyncSessionLocal

# Import base - will be created in __init__.py
from app.db.models import Base


class Media(Base):
    """Media model representing photos and videos."""

    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    original_blob_path: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_blob_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
    )
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="Duration in seconds for videos",
    )

    # AI processing fields
    ai_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    ai_processing_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    ai_tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Raw AI response with tags",
    )
    last_ai_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Embedding for semantic search (pgvector)
    # Note: Using ARRAY type for now. For production, use pgvector Vector(1536) type
    # after installing pgvector extension: CREATE EXTENSION vector;
    # Then use: from pgvector.sqlalchemy import Vector
    # embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(1536), nullable=True)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        ARRAY(Float),
        nullable=True,
        comment="Vector embedding for semantic search (1536 dimensions for text-embedding-3-small)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="media",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Media(id={self.id}, filename={self.filename})>"

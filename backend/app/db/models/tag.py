"""Tag model for media tags."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import Base


class Tag(Base):
    """Tag model for media tags (AI-generated or manual)."""

    __tablename__ = "tag"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score for AI-generated tags",
    )
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ai",
        index=True,
        comment="Source of tag: 'ai' or 'manual'",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    media: Mapped["Media"] = relationship("Media", back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, tag_name={self.tag_name}, source={self.source})>"

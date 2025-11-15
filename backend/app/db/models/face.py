"""Face model for detected faces in media."""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.models import Base, UUIDMixin, TimestampMixin


class Face(Base, UUIDMixin, TimestampMixin):
    """Detected face in a media item."""

    __tablename__ = "face"

    media_id: Mapped[UUID] = mapped_column(
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Face embedding for similarity matching (512 or 128 dimensions depending on model)
    face_embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(512),
        nullable=True,
    )

    # Bounding box coordinates (JSON: {x, y, width, height})
    bounding_box: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    # Clustering
    cluster_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,  # For grouping faces by person
    )

    # Person identification (manual or AI-assigned)
    person_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Relationships
    media: Mapped["Media"] = relationship("Media", back_populates="faces")

    def __repr__(self) -> str:
        return f"<Face in media {self.media_id} (cluster {self.cluster_id})>"

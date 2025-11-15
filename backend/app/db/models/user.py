"""User model for family members."""

from enum import Enum

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import Base, UUIDMixin, TimestampMixin


class UserRole(str, Enum):
    """User roles for family members."""

    ADMIN = "admin"  # Full access, can manage users
    MEMBER = "member"  # Can upload, edit own content
    VIEWER = "viewer"  # Read-only access


class User(Base, UUIDMixin, TimestampMixin):
    """Family member user account."""

    __tablename__ = "user"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.MEMBER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    media: Mapped[list["Media"]] = relationship(
        "Media",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    albums: Mapped[list["Album"]] = relationship(
        "Album",
        back_populates="created_by_user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

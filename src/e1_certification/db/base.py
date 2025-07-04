"""
Base classes for SQLAlchemy models.
Simple base with optional timestamp tracking.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        Converts CamelCase to snake_case.
        """
        name = cls.__name__
        # Convert CamelCase to snake_case
        result = []
        for i, char in enumerate(name):
            if i > 0 and char.isupper():
                result.append("_")
            result.append(char.lower())
        # Make the name plural
        return "".join(result) + "s"

    def __repr__(self) -> str:
        """String representation of model instance."""
        attrs = []
        for col in self.__table__.columns:
            attrs.append(f"{col.name}={getattr(self, col.name)}")
        return f"<{self.__class__.__name__}({', '.join(attrs)})"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


class TimestampMixin:
    """Optional mixin for tracking when records are created/updated in our database."""

    created_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC), nullable=False
    )

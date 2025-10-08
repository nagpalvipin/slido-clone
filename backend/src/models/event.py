"""
Event model representing course sessions or presentations.

Handles event creation, slug validation, and host authentication.
"""

import secrets
import string

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class Event(Base):
    """Event model for course sessions and presentations."""

    __tablename__ = "events"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic information
    title = Column(String(200), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Access codes
    short_code = Column(String(8), unique=True, nullable=False, index=True)
    host_code = Column(String(50), unique=True, nullable=False, index=True)  # UNIQUE constraint for custom codes

    # Timestamps and status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    polls = relationship("Poll", back_populates="event", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="event", cascade="all, delete-orphan")
    attendees = relationship("Attendee", back_populates="event", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize event with auto-generated codes."""
        super().__init__(**kwargs)
        if not self.short_code:
            self.short_code = self._generate_short_code()
        if not self.host_code:
            self.host_code = self._generate_host_code()

    @staticmethod
    def _generate_short_code() -> str:
        """Generate 8-character alphanumeric short code."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(8))

    @staticmethod
    def _generate_host_code() -> str:
        """Generate secure host authentication code."""
        chars = string.ascii_lowercase + string.digits
        random_part = ''.join(secrets.choice(chars) for _ in range(12))
        return f"host_{random_part}"

    @property
    def attendee_count(self) -> int:
        """Count of attendees for this event."""
        return len(self.attendees)

    def __repr__(self):
        return f"<Event(id={self.id}, slug='{self.slug}', title='{self.title}')>"

"""
Attendee model for anonymous session tracking.

Tracks anonymous attendees for vote deduplication and session management.
"""

import secrets
import string

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class Attendee(Base):
    """Attendee model for anonymous session tracking."""

    __tablename__ = "attendees"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # Session tracking
    session_id = Column(String(32), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("Event", back_populates="attendees")
    questions = relationship("Question", back_populates="attendee", cascade="all, delete-orphan")
    question_votes = relationship("QuestionVote", back_populates="attendee", cascade="all, delete-orphan")
    poll_responses = relationship("PollResponse", back_populates="attendee", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize attendee with auto-generated session ID."""
        super().__init__(**kwargs)
        if not self.session_id:
            self.session_id = self._generate_session_id()

    @staticmethod
    def _generate_session_id() -> str:
        """Generate secure session ID for anonymous tracking."""
        chars = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(32))

    def __repr__(self):
        return f"<Attendee(id={self.id}, event_id={self.event_id}, session='{self.session_id[:8]}...')>"

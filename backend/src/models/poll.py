"""
Poll model for managing polls within events.

Supports single-choice and multi-choice polls with status management.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class PollType(enum.Enum):
    """Poll type enumeration."""
    single = "single"
    multiple = "multiple"


class PollStatus(enum.Enum):
    """Poll status enumeration."""
    draft = "draft"
    active = "active"
    closed = "closed"


class Poll(Base):
    """Poll model for event polling."""

    __tablename__ = "polls"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # Poll content
    question_text = Column(Text, nullable=False)
    poll_type = Column(Enum(PollType), nullable=False, default=PollType.single)
    status = Column(Enum(PollStatus), nullable=False, default=PollStatus.draft)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("Event", back_populates="polls")
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    responses = relationship("PollResponse", back_populates="poll", cascade="all, delete-orphan")

    @property
    def total_votes(self) -> int:
        """Total number of votes across all options."""
        return sum(option.vote_count for option in self.options)

    def __repr__(self):
        return f"<Poll(id={self.id}, event_id={self.event_id}, question='{self.question_text[:50]}...')>"

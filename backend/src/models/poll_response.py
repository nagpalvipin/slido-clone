"""
PollResponse model for tracking individual votes.

Records attendee votes on poll options.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class PollResponse(Base):
    """Poll response model for tracking votes."""

    __tablename__ = "poll_responses"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    option_id = Column(Integer, ForeignKey("poll_options.id"), nullable=False)
    attendee_id = Column(Integer, ForeignKey("attendees.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    poll = relationship("Poll", back_populates="responses")
    option = relationship("PollOption", back_populates="responses")
    attendee = relationship("Attendee", back_populates="poll_responses")

    def __repr__(self):
        return f"<PollResponse(id={self.id}, poll_id={self.poll_id}, option_id={self.option_id})>"

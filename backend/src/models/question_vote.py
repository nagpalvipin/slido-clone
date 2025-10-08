"""
QuestionVote model for question upvoting.

Tracks attendee upvotes on questions for prioritization.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class QuestionVote(Base):
    """Question vote model for upvoting questions."""

    __tablename__ = "question_votes"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    attendee_id = Column(Integer, ForeignKey("attendees.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    question = relationship("Question", back_populates="votes")
    attendee = relationship("Attendee", back_populates="question_votes")

    def __repr__(self):
        return f"<QuestionVote(id={self.id}, question_id={self.question_id}, attendee_id={self.attendee_id})>"

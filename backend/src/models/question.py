"""
Question model for Q&A functionality.

Handles attendee questions with moderation and upvoting.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base
import enum


class QuestionStatus(enum.Enum):
    """Question status enumeration."""
    submitted = "submitted"
    approved = "approved"
    answered = "answered"
    rejected = "rejected"


class Question(Base):
    """Question model for Q&A functionality."""
    
    __tablename__ = "questions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    attendee_id = Column(Integer, ForeignKey("attendees.id"), nullable=False)
    
    # Question content
    question_text = Column(Text, nullable=False)
    status = Column(Enum(QuestionStatus), nullable=False, default=QuestionStatus.submitted)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="questions")
    attendee = relationship("Attendee", back_populates="questions")
    votes = relationship("QuestionVote", back_populates="question", cascade="all, delete-orphan")
    
    @property
    def upvote_count(self) -> int:
        """Count of upvotes for this question."""
        return len(self.votes)
    
    def __repr__(self):
        return f"<Question(id={self.id}, event_id={self.event_id}, text='{self.question_text[:50]}...')>"
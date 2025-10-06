"""
PollOption model for individual poll choices.

Each poll option represents a selectable choice within a poll.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base


class PollOption(Base):
    """Poll option model for individual poll choices."""
    
    __tablename__ = "poll_options"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    
    # Option content
    option_text = Column(String(500), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    
    # Relationships
    poll = relationship("Poll", back_populates="options")
    responses = relationship("PollResponse", back_populates="option", cascade="all, delete-orphan")
    
    @property
    def vote_count(self) -> int:
        """Count of votes for this option."""
        return len(self.responses)
    
    def __repr__(self):
        return f"<PollOption(id={self.id}, poll_id={self.poll_id}, text='{self.option_text}')>"
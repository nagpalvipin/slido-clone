"""
Question service for Q&A management and moderation logic.

Handles question submission, moderation, and upvoting.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Any
from src.models.question import Question, QuestionStatus
from src.models.question_vote import QuestionVote
from src.models.attendee import Attendee


class QuestionService:
    """Service class for question operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def submit_question(self, event_id: int, question_text: str, attendee_session_id: str) -> Question:
        """Submit a new question from an attendee."""
        # Validate input
        if not question_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Question text is required"
            )
        
        if len(question_text.strip()) > 1000:  # Constitutional limit
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Question text must be max 1000 characters"
            )
        
        # Get or create attendee
        attendee = self.db.query(Attendee).filter(
            Attendee.session_id == attendee_session_id,
            Attendee.event_id == event_id
        ).first()
        
        if not attendee:
            attendee = Attendee(
                event_id=event_id,
                session_id=attendee_session_id
            )
            self.db.add(attendee)
            self.db.flush()
        
        # Create question
        question = Question(
            event_id=event_id,
            attendee_id=attendee.id,
            question_text=question_text.strip()
        )
        
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def moderate_question(self, question_id: int, status: str) -> Question:
        """Moderate a question (host action)."""
        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Validate status
        try:
            status_enum = QuestionStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status must be 'submitted', 'approved', 'answered', or 'rejected'"
            )
        
        question.status = status_enum
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def upvote_question(self, question_id: int, attendee_session_id: str, event_id: int) -> Dict[str, Any]:
        """Upvote a question."""
        # Get question
        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Get or create attendee
        attendee = self.db.query(Attendee).filter(
            Attendee.session_id == attendee_session_id,
            Attendee.event_id == event_id
        ).first()
        
        if not attendee:
            attendee = Attendee(
                event_id=event_id,
                session_id=attendee_session_id
            )
            self.db.add(attendee)
            self.db.flush()
        
        # Check for existing upvote
        existing_vote = self.db.query(QuestionVote).filter(
            QuestionVote.question_id == question_id,
            QuestionVote.attendee_id == attendee.id
        ).first()
        
        if existing_vote:
            # Remove upvote (toggle)
            self.db.delete(existing_vote)
            action = "removed"
        else:
            # Add upvote
            vote = QuestionVote(
                question_id=question_id,
                attendee_id=attendee.id
            )
            self.db.add(vote)
            action = "added"
        
        self.db.commit()
        
        # Get updated count
        self.db.refresh(question)
        
        return {
            "action": action,
            "question_id": question_id,
            "upvote_count": question.upvote_count
        }
    
    def get_questions_for_event(self, event_id: int) -> List[Question]:
        """Get all questions for an event, ordered by upvotes."""
        return self.db.query(Question).filter(
            Question.event_id == event_id
        ).order_by(Question.upvote_count.desc(), Question.created_at.asc()).all()
    
    def get_questions_for_moderation(self, event_id: int) -> List[Question]:
        """Get questions needing moderation (host view)."""
        return self.db.query(Question).filter(
            Question.event_id == event_id,
            Question.status == QuestionStatus.submitted
        ).order_by(Question.upvote_count.desc(), Question.created_at.asc()).all()
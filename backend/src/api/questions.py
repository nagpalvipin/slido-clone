"""
Questions API router for Q&A management endpoints.

Handles question submission, moderation, and upvoting.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid

from src.core.database import get_db
from src.core.security import SecurityUtils
from src.services.event_service import EventService
from src.services.question_service import QuestionService
from src.models.question import QuestionStatus

router = APIRouter(prefix="/api/v1", tags=["questions"])


# Pydantic models for request/response
class QuestionSubmitRequest(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=1000)


class QuestionModerationRequest(BaseModel):
    status: str = Field(..., pattern="^(submitted|approved|answered|rejected)$")


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    status: str
    created_at: str
    upvote_count: int
    
    class Config:
        from_attributes = True


def get_attendee_session_id(request: Request) -> str:
    """Get or create attendee session ID."""
    session_id = request.headers.get("x-session-id")
    if not session_id:
        # Generate a new session ID if not provided
        session_id = str(uuid.uuid4()).replace("-", "")
    return session_id


@router.post("/events/{event_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def submit_question(
    event_id: int,
    question_data: QuestionSubmitRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit a new question (attendee action)."""
    # Get attendee session ID
    session_id = get_attendee_session_id(request)
    
    # Submit question
    question_service = QuestionService(db)
    question = question_service.submit_question(
        event_id=event_id,
        question_text=question_data.question_text,
        attendee_session_id=session_id
    )
    
    return QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        status=question.status.value,
        created_at=question.created_at.isoformat() + "Z",
        upvote_count=question.upvote_count
    )


@router.post("/events/{event_id}/questions/{question_id}/upvote")
async def upvote_question(
    event_id: int,
    question_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Upvote a question (attendee action)."""
    # Get attendee session ID
    session_id = get_attendee_session_id(request)
    
    # Record upvote
    question_service = QuestionService(db)
    result = question_service.upvote_question(question_id, session_id, event_id)
    
    return result


@router.put("/events/{event_id}/questions/{question_id}/status", response_model=QuestionResponse)
async def moderate_question(
    event_id: int,
    question_id: int,
    moderation_data: QuestionModerationRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Moderate a question (host only)."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    try:
        host_code = SecurityUtils.extract_host_code_from_header(authorization)
    except HTTPException:
        raise
    
    # Verify host has access to event
    event_service = EventService(db)
    event = event_service.verify_host_access(event_id, host_code)
    
    # Moderate question
    question_service = QuestionService(db)
    question = question_service.moderate_question(question_id, moderation_data.status)
    
    # Verify question belongs to event
    if question.event_id != event_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in this event"
        )
    
    return QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        status=question.status.value,
        created_at=question.created_at.isoformat() + "Z",
        upvote_count=question.upvote_count
    )


@router.get("/events/{event_id}/questions", response_model=List[QuestionResponse])
async def get_event_questions(
    event_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get all questions for an event (host view)."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    try:
        host_code = SecurityUtils.extract_host_code_from_header(authorization)
    except HTTPException:
        raise
    
    # Verify host has access to event
    event_service = EventService(db)
    event = event_service.verify_host_access(event_id, host_code)
    
    # Get questions
    question_service = QuestionService(db)
    questions = question_service.get_questions_for_event(event_id)
    
    return [
        QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            status=q.status.value,
            created_at=q.created_at.isoformat() + "Z",
            upvote_count=q.upvote_count
        )
        for q in questions
    ]
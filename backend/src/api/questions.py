"""
Questions API router for Q&A management endpoints.

Handles question submission and upvoting. All questions are automatically approved.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import SecurityUtils
from src.services.event_service import EventService
from src.services.question_service import QuestionService
from src.api import websocket

router = APIRouter(prefix="/api/v1", tags=["questions"])


# Pydantic models for request/response
class QuestionSubmitRequest(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=1000)


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    created_at: str
    upvote_count: int
    is_answered: bool = False

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

    response = QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        created_at=question.created_at.isoformat() + "Z",
        upvote_count=question.upvote_count
    )

    # Broadcast question creation via WebSocket
    await websocket.broadcast_question_submitted(event_id, response.model_dump())

    return response


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

    # Broadcast upvote via WebSocket
    await websocket.broadcast_question_upvoted(event_id, question_id, result["upvote_count"])

    return result


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
            created_at=q.created_at.isoformat() + "Z",
            upvote_count=q.upvote_count
        )
        for q in questions
    ]


@router.get("/events/{event_id}/questions/public", response_model=List[QuestionResponse])
async def get_public_questions(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get all questions for an event (public attendee view - no auth required)."""
    # Verify event exists
    event_service = EventService(db)
    event = event_service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Get all questions (all questions are public now)
    question_service = QuestionService(db)
    questions = question_service.get_questions_for_event(event_id)

    return [
        QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            created_at=q.created_at.isoformat() + "Z",
            upvote_count=q.upvote_count,
            is_answered=q.is_answered
        )
        for q in questions
    ]


@router.get("/events/slug/{event_slug}/questions/public", response_model=List[QuestionResponse])
async def get_public_questions_by_slug(
    event_slug: str,
    db: Session = Depends(get_db)
):
    """Get all questions for an event by slug (public attendee view - no auth required)."""
    # Get event by slug
    event_service = EventService(db)
    event = event_service.get_event_by_slug(event_slug)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Get all questions
    question_service = QuestionService(db)
    questions = question_service.get_questions_for_event(event.id)

    return [
        QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            created_at=q.created_at.isoformat() + "Z",
            upvote_count=q.upvote_count,
            is_answered=q.is_answered
        )
        for q in questions
    ]


@router.put("/events/{event_id}/questions/{question_id}/answered", response_model=QuestionResponse)
async def toggle_question_answered(
    event_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    x_host_code: Optional[str] = Header(None, alias="x-host-code")
):
    """Toggle question answered status (host only)."""
    # Validate host code
    if not x_host_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event host can mark questions as answered"
        )
    
    # Verify event exists and host has access
    event_service = EventService(db)
    event = event_service.verify_host_access(event_id, x_host_code)
    
    # Toggle answered status
    question_service = QuestionService(db)
    question = question_service.toggle_answered(question_id, event_id)
    
    return QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        created_at=question.created_at.isoformat() + "Z",
        upvote_count=question.upvote_count,
        is_answered=question.is_answered
    )

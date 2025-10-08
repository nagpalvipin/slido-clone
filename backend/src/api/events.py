"""
Events API router for event management endpoints.

Handles event creation, retrieval, and host access.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import SecurityUtils
from src.services.event_service import EventService

router = APIRouter(prefix="/api/v1/events", tags=["events"])


# Pydantic models for request/response
class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    host_code: Optional[str] = Field(None, description="Optional custom host code (3-30 alphanumeric characters, hyphens, underscores). Auto-prefixed with 'host_'.")


class EventResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class EventCreateResponse(EventResponse):
    short_code: str
    host_code: str
    created_at: str
    attendee_count: int


class EventHostResponse(EventCreateResponse):
    polls: List[Dict[str, Any]] = []
    questions: List[Dict[str, Any]] = []


@router.post("/", response_model=EventCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new event.

    Accepts optional custom host_code. If not provided, auto-generates secure code.
    """
    service = EventService(db)
    event = service.create_event(
        title=event_data.title,
        slug=event_data.slug,
        description=event_data.description,
        host_code=event_data.host_code  # Pass custom host_code if provided
    )

    return EventCreateResponse(
        id=event.id,
        title=event.title,
        slug=event.slug,
        short_code=event.short_code,
        host_code=event.host_code,
        description=event.description,
        created_at=event.created_at.isoformat() + "Z",
        is_active=event.is_active,
        attendee_count=event.attendee_count
    )


@router.get("/{slug}", response_model=EventResponse)
async def get_event(slug: str, db: Session = Depends(get_db)):
    """Get event details for attendee joining."""
    service = EventService(db)
    event = service.get_event_by_slug(slug)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return EventResponse(
        id=event.id,
        title=event.title,
        slug=event.slug,
        description=event.description,
        is_active=event.is_active
    )


@router.get("/{slug}/host", response_model=EventHostResponse)
async def get_host_view(
    slug: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get event details for host access."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )

    try:
        host_code = SecurityUtils.extract_host_code_from_header(authorization)
    except HTTPException:
        raise

    service = EventService(db)
    event = service.get_event_for_host(slug, host_code)

    # Format polls for response
    polls_data = []
    for poll in event.polls:
        poll_dict = {
            "id": poll.id,
            "question_text": poll.question_text,
            "poll_type": poll.poll_type.value,
            "status": poll.status.value,
            "created_at": poll.created_at.isoformat() + "Z",
            "options": [
                {
                    "id": opt.id,
                    "option_text": opt.option_text,
                    "position": opt.position,
                    "vote_count": opt.vote_count
                }
                for opt in sorted(poll.options, key=lambda x: x.position)
            ]
        }
        polls_data.append(poll_dict)

    # Format questions for response
    questions_data = []
    for question in event.questions:
        question_dict = {
            "id": question.id,
            "question_text": question.question_text,
            "created_at": question.created_at.isoformat() + "Z",
            "upvote_count": question.upvote_count
        }
        questions_data.append(question_dict)

    return EventHostResponse(
        id=event.id,
        title=event.title,
        slug=event.slug,
        short_code=event.short_code,
        host_code=event.host_code,
        description=event.description,
        created_at=event.created_at.isoformat() + "Z",
        is_active=event.is_active,
        attendee_count=event.attendee_count,
        polls=polls_data,
        questions=questions_data
    )


@router.get("/host/{host_code}", response_model=Dict[str, Any])
async def get_events_by_host(
    host_code: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all events for a specific host code with pagination."""
    service = EventService(db)
    events, total = service.get_events_by_host_code(host_code, limit, offset)
    
    # Format events for response
    events_data = []
    for event in events:
        event_dict = {
            "id": event.id,
            "title": event.title,
            "slug": event.slug,
            "host_code": event.host_code,
            "created_at": event.created_at.isoformat() + "Z",
            "is_active": event.is_active,
            "question_count": len(event.questions) if event.questions else 0
        }
        events_data.append(event_dict)
    
    return {
        "events": events_data,
        "total": total
    }


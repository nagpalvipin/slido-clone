"""
Polls API router for poll management endpoints.

Handles poll creation, status updates, voting, and results.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid

from src.core.database import get_db
from src.core.security import SecurityUtils
from src.services.event_service import EventService
from src.services.poll_service import PollService
from src.models.poll import PollType, PollStatus

router = APIRouter(prefix="/api/v1", tags=["polls"])


# Pydantic models for request/response
class PollOptionRequest(BaseModel):
    option_text: str = Field(..., min_length=1, max_length=500)
    position: int = Field(..., ge=0)


class PollCreateRequest(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=1000)
    poll_type: str = Field(..., pattern="^(single|multiple)$")
    options: List[PollOptionRequest] = Field(..., min_length=2, max_length=10)


class PollStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(draft|active|closed)$")


class VoteRequest(BaseModel):
    option_id: int


class PollOptionResponse(BaseModel):
    id: int
    option_text: str
    position: int
    vote_count: int
    
    class Config:
        from_attributes = True


class PollResponse(BaseModel):
    id: int
    question_text: str
    poll_type: str
    status: str
    created_at: str
    options: List[PollOptionResponse]
    
    class Config:
        from_attributes = True


def get_attendee_session_id(request: Request) -> str:
    """Get or create attendee session ID."""
    session_id = request.headers.get("x-session-id")
    if not session_id:
        # Generate a new session ID if not provided
        session_id = str(uuid.uuid4()).replace("-", "")
    return session_id


@router.post("/events/{event_id}/polls", response_model=PollResponse, status_code=status.HTTP_201_CREATED)
async def create_poll(
    event_id: int,
    poll_data: PollCreateRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Create a new poll (host only)."""
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
    
    # Create poll
    poll_service = PollService(db)
    # Convert options to dict format expected by service
    options_data = [opt.model_dump() for opt in poll_data.options]
    
    poll = poll_service.create_poll(
        event_id=event_id,
        question_text=poll_data.question_text,
        poll_type=poll_data.poll_type,
        options=options_data
    )
    
    return PollResponse(
        id=poll.id,
        question_text=poll.question_text,
        poll_type=poll.poll_type.value,
        status=poll.status.value,
        created_at=poll.created_at.isoformat() + "Z",
        options=[
            PollOptionResponse(
                id=opt.id,
                option_text=opt.option_text,
                position=opt.position,
                vote_count=opt.vote_count
            )
            for opt in sorted(poll.options, key=lambda x: x.position)
        ]
    )


@router.put("/events/{event_id}/polls/{poll_id}/status", response_model=PollResponse)
async def update_poll_status(
    event_id: int,
    poll_id: int,
    status_data: PollStatusUpdateRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Update poll status (host only)."""
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
    
    # Update poll status
    poll_service = PollService(db)
    poll = poll_service.update_poll_status(poll_id, status_data.status)
    
    # Verify poll belongs to event
    if poll.event_id != event_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found in this event"
        )
    
    return PollResponse(
        id=poll.id,
        question_text=poll.question_text,
        poll_type=poll.poll_type.value,
        status=poll.status.value,
        created_at=poll.created_at.isoformat() + "Z",
        options=[
            PollOptionResponse(
                id=opt.id,
                option_text=opt.option_text,
                position=opt.position,
                vote_count=opt.vote_count
            )
            for opt in sorted(poll.options, key=lambda x: x.position)
        ]
    )


@router.post("/events/{event_id}/polls/{poll_id}/vote")
async def vote_on_poll(
    event_id: int,
    poll_id: int,
    vote_data: VoteRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Vote on a poll (attendee action)."""
    # Get attendee session ID
    session_id = get_attendee_session_id(request)
    
    # Record vote
    poll_service = PollService(db)
    result = poll_service.vote_on_poll(poll_id, vote_data.option_id, session_id)
    
    return result


@router.get("/events/{event_id}/polls/{poll_id}/results")
async def get_poll_results(
    event_id: int,
    poll_id: int,
    db: Session = Depends(get_db)
):
    """Get poll results."""
    poll_service = PollService(db)
    return poll_service.get_poll_results(poll_id)
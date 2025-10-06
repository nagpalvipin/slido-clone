"""
Event service for CRUD operations and business logic.

Handles event creation, retrieval, and management operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional, List
from src.models.event import Event
from src.core.security import SecurityUtils


class EventService:
    """Service class for event operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_event(self, title: str, slug: str, description: Optional[str] = None) -> Event:
        """Create a new event with validation."""
        # Validate input
        if not SecurityUtils.validate_title(title):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Title must be 1-200 characters"
            )
        
        if not SecurityUtils.validate_slug(slug):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Slug must be 3-50 characters, alphanumeric and hyphens only"
            )
        
        if not SecurityUtils.validate_description(description):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Description must be max 1000 characters"
            )
        
        # Create event
        event = Event(
            title=title.strip(),
            slug=slug.lower(),
            description=description.strip() if description else None
        )
        
        try:
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Event slug already exists"
            )
    
    def get_event_by_slug(self, slug: str) -> Optional[Event]:
        """Get event by slug for attendee access."""
        return self.db.query(Event).filter(Event.slug == slug).first()
    
    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Get event by ID."""
        return self.db.query(Event).filter(Event.id == event_id).first()
    
    def get_event_for_host(self, slug: str, host_code: str) -> Event:
        """Get event for host access with authentication."""
        event = self.get_event_by_slug(slug)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        if event.host_code != host_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid host code"
            )
        
        return event
    
    def verify_host_access(self, event_id: int, host_code: str) -> Event:
        """Verify host has access to event."""
        event = self.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        if event.host_code != host_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid host code"
            )
        
        return event
    
    def list_events(self, limit: int = 100) -> List[Event]:
        """List events (for admin/debugging purposes)."""
        return self.db.query(Event).limit(limit).all()
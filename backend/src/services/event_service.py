"""
Event service for CRUD operations and business logic.

Handles event creation, retrieval, and management operations.
"""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.security import SecurityUtils
from src.core.validation import sanitize_host_code, validate_host_code
from src.models.event import Event


class EventService:
    """Service class for event operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_event(self, title: str, slug: str, description: Optional[str] = None,
                    host_code: Optional[str] = None) -> Event:
        """
        Create a new event with validation.

        Args:
            title: Event title (1-200 chars)
            slug: Event slug (3-50 chars, alphanumeric + hyphens)
            description: Optional description (max 1000 chars)
            host_code: Optional custom host code (format: host_[a-z0-9]{12})
                      If not provided, will be auto-generated

        Returns:
            Created Event object

        Raises:
            HTTPException: 422 for validation errors, 409 for duplicates
        """
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

        # Validate and sanitize custom host code if provided
        sanitized_host_code = None
        if host_code:
            if not validate_host_code(host_code):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Host code must be 3-30 characters (alphanumeric, hyphens, underscores only)"
                )
            sanitized_host_code = sanitize_host_code(host_code)

        # Create event (will auto-generate host_code if not provided)
        event = Event(
            title=title.strip(),
            slug=slug.lower(),
            description=description.strip() if description else None
        )

        # Set custom host code if provided (after Event init to override auto-generation)
        if sanitized_host_code:
            event.host_code = sanitized_host_code

        try:
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except IntegrityError as e:
            self.db.rollback()
            error_msg = str(e.orig)

            # Check if it's a host_code duplicate
            if 'host_code' in error_msg.lower() or (host_code and host_code in error_msg):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Host code '{sanitized_host_code}' is already in use. Please choose a different code."
                )
            # Otherwise it's a slug duplicate
            else:
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
    
    def get_events_by_host_code(
        self, 
        host_code: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> tuple[List[Event], int]:
        """
        Get events for a specific host_code with pagination.
        
        Returns:
            Tuple of (events_list, total_count)
        """
        query = self.db.query(Event).filter(Event.host_code == host_code)
        total = query.count()
        events = query.order_by(Event.created_at.desc()).limit(limit).offset(offset).all()
        return events, total

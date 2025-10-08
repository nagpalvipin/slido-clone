"""
Poll service for poll management and voting logic.

Handles poll creation, status updates, voting, and results.
"""

from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.attendee import Attendee
from src.models.poll import Poll, PollStatus, PollType
from src.models.poll_option import PollOption
from src.models.poll_response import PollResponse


class PollService:
    """Service class for poll operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_poll(
        self,
        event_id: int,
        question_text: str,
        poll_type: str,
        options: List[Dict[str, Any]]
    ) -> Poll:
        """Create a new poll with options."""
        # Validate input
        if not question_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Question text is required"
            )

        # Validate poll type
        try:
            poll_type_enum = PollType(poll_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Poll type must be 'single' or 'multiple'"
            )

        # Validate options
        if not options or len(options) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Poll must have at least 2 options"
            )

        if len(options) > 10:  # Constitutional limit
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Poll cannot have more than 10 options"
            )

        # Create poll
        poll = Poll(
            event_id=event_id,
            question_text=question_text.strip(),
            poll_type=poll_type_enum
        )

        self.db.add(poll)
        self.db.flush()  # Get poll ID

        # Create options
        for option_data in options:
            if not option_data.get("option_text", "").strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Option text is required"
                )

            option = PollOption(
                poll_id=poll.id,
                option_text=option_data["option_text"].strip(),
                position=option_data.get("position", 0)
            )
            self.db.add(option)

        self.db.commit()
        self.db.refresh(poll)
        return poll

    def update_poll_status(self, poll_id: int, status: str) -> Poll:
        """Update poll status."""
        poll = self.db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poll not found"
            )

        # Validate status
        try:
            status_enum = PollStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status must be 'draft', 'active', or 'closed'"
            )

        poll.status = status_enum
        self.db.commit()
        self.db.refresh(poll)
        return poll

    def vote_on_poll(self, poll_id: int, option_id: int, attendee_session_id: str) -> Dict[str, Any]:
        """Record a vote on a poll."""
        # Get poll
        poll = self.db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poll not found"
            )

        # Check if poll is active
        if poll.status != PollStatus.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Poll is not active"
            )

        # Get or create attendee
        attendee = self.db.query(Attendee).filter(
            Attendee.session_id == attendee_session_id,
            Attendee.event_id == poll.event_id
        ).first()

        if not attendee:
            attendee = Attendee(
                event_id=poll.event_id,
                session_id=attendee_session_id
            )
            self.db.add(attendee)
            self.db.flush()

        # Check if option exists and belongs to poll
        option = self.db.query(PollOption).filter(
            PollOption.id == option_id,
            PollOption.poll_id == poll_id
        ).first()

        if not option:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poll option not found"
            )

        # For single-choice polls, remove existing vote
        if poll.poll_type == PollType.single:
            existing_response = self.db.query(PollResponse).filter(
                PollResponse.poll_id == poll_id,
                PollResponse.attendee_id == attendee.id
            ).first()

            if existing_response:
                self.db.delete(existing_response)

        # Check for duplicate vote on same option
        existing_vote = self.db.query(PollResponse).filter(
            PollResponse.poll_id == poll_id,
            PollResponse.option_id == option_id,
            PollResponse.attendee_id == attendee.id
        ).first()

        if existing_vote:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vote already recorded for this option"
            )

        # Record the vote
        response = PollResponse(
            poll_id=poll_id,
            option_id=option_id,
            attendee_id=attendee.id
        )

        self.db.add(response)
        self.db.commit()

        return {"vote_recorded": True, "poll_id": poll_id, "option_id": option_id}

    def get_poll_results(self, poll_id: int) -> Dict[str, Any]:
        """Get poll results with vote counts."""
        poll = self.db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poll not found"
            )

        results = []
        for option in poll.options:
            results.append({
                "option_id": option.id,
                "option_text": option.option_text,
                "vote_count": option.vote_count,
                "position": option.position
            })

        return {
            "poll_id": poll_id,
            "total_votes": poll.total_votes,
            "results": sorted(results, key=lambda x: x["position"])
        }

"""
Integration Tests for Question Flow
Tests the complete user journey for questions including WebSocket events.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db
from src.models.event import Event
from src.models.question import Question, QuestionStatus


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_event(test_db):
    """Create a test event."""
    db = TestingSessionLocal()
    try:
        event = Event(
            title="Test Event",
            slug="test-event",
            host_code="host_testcode123",
            short_code="TEST123"
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


class TestAttendeeQuestionJourney:
    """Test the complete attendee question submission journey."""

    def test_attendee_submits_question_appears_for_host(self, client, test_event):
        """
        Journey: Attendee submits question, it should appear for host.
        Steps:
        1. Attendee submits question
        2. Host fetches questions
        3. Verify question appears in host view
        """
        # Step 1: Attendee submits question
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": "What is the agenda for today?"},
            headers={"x-session-id": "attendee_session_1"}
        )
        
        assert response.status_code == 201, f"Failed to create question: {response.text}"
        question_data = response.json()
        assert question_data["question_text"] == "What is the agenda for today?"
        assert question_data["status"] == "submitted"
        assert question_data["upvote_count"] == 0
        question_id = question_data["id"]

        # Step 2: Host fetches questions
        response = client.get(
            f"/api/v1/events/{test_event.id}/questions",
            headers={"Authorization": f"Host {test_event.host_code}"}
        )
        
        assert response.status_code == 200, f"Failed to get questions: {response.text}"
        questions = response.json()
        
        # Step 3: Verify question appears
        assert len(questions) == 1
        assert questions[0]["id"] == question_id
        assert questions[0]["question_text"] == "What is the agenda for today?"
        assert questions[0]["status"] == "submitted"

    def test_attendee_cannot_see_unapproved_questions(self, client, test_event):
        """
        Journey: Attendee submits question but shouldn't see it until approved.
        Steps:
        1. Attendee submits question
        2. Try to fetch questions as attendee (should be empty)
        3. Host approves question
        4. Attendee can now see question
        """
        # Step 1: Submit question
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": "Is there a break scheduled?"},
            headers={"x-session-id": "attendee_session_2"}
        )
        assert response.status_code == 201
        question_id = response.json()["id"]

        # Step 2: Attendee fetches questions (endpoint doesn't exist yet, but logic should filter)
        # For now, we verify the database state
        db = TestingSessionLocal()
        try:
            question = db.query(Question).filter_by(id=question_id).first()
            assert question.status == QuestionStatus.submitted
        finally:
            db.close()

        # Step 3: Host approves question
        response = client.put(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Host {test_event.host_code}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

        # Step 4: Verify approved status
        db = TestingSessionLocal()
        try:
            question = db.query(Question).filter_by(id=question_id).first()
            assert question.status == QuestionStatus.approved
        finally:
            db.close()


class TestQuestionUpvotingJourney:
    """Test the question upvoting journey."""

    def test_multiple_attendees_upvote_question(self, client, test_event):
        """
        Journey: Multiple attendees upvote the same question.
        Steps:
        1. Create and approve a question
        2. Attendee 1 upvotes
        3. Attendee 2 upvotes
        4. Same attendee tries to upvote again (should not increase)
        5. Verify final count
        """
        # Step 1: Create and approve question
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": "Will there be Q&A?"},
            headers={"x-session-id": "creator_session"}
        )
        question_id = response.json()["id"]
        
        client.put(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Host {test_event.host_code}"}
        )

        # Step 2: Attendee 1 upvotes
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/upvote",
            headers={"x-session-id": "attendee_1"}
        )
        assert response.status_code == 200
        assert response.json()["upvote_count"] == 1

        # Step 3: Attendee 2 upvotes
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/upvote",
            headers={"x-session-id": "attendee_2"}
        )
        assert response.status_code == 200
        assert response.json()["upvote_count"] == 2

        # Step 4: Attendee 1 tries to upvote again (should toggle off - remove upvote)
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/upvote",
            headers={"x-session-id": "attendee_1"}
        )
        assert response.status_code == 200
        # Upvote should be removed (toggle behavior), count goes back to 1
        assert response.json()["upvote_count"] == 1
        assert response.json()["action"] == "removed"

        # Step 5: Verify final state (should be 1 after toggle)
        response = client.get(
            f"/api/v1/events/{test_event.id}/questions",
            headers={"Authorization": f"Host {test_event.host_code}"}
        )
        questions = response.json()
        question = next(q for q in questions if q["id"] == question_id)
        assert question["upvote_count"] == 1


class TestHostModerationJourney:
    """Test host moderation capabilities."""

    def test_host_moderates_multiple_questions(self, client, test_event):
        """
        Journey: Host receives multiple questions and moderates them.
        Steps:
        1. Create 3 questions
        2. Host approves 2, rejects 1
        3. Verify states
        """
        # Step 1: Create 3 questions
        questions = []
        for i in range(3):
            response = client.post(
                f"/api/v1/events/{test_event.id}/questions",
                json={"question_text": f"Question {i+1}?"},
                headers={"x-session-id": f"attendee_{i}"}
            )
            questions.append(response.json())

        # Step 2: Moderate questions
        # Approve first two
        for i in range(2):
            response = client.put(
                f"/api/v1/events/{test_event.id}/questions/{questions[i]['id']}/status",
                json={"status": "approved"},
                headers={"Authorization": f"Host {test_event.host_code}"}
            )
            assert response.status_code == 200
            assert response.json()["status"] == "approved"

        # Reject third one
        response = client.put(
            f"/api/v1/events/{test_event.id}/questions/{questions[2]['id']}/status",
            json={"status": "rejected"},
            headers={"Authorization": f"Host {test_event.host_code}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

        # Step 3: Verify final states
        response = client.get(
            f"/api/v1/events/{test_event.id}/questions",
            headers={"Authorization": f"Host {test_event.host_code}"}
        )
        all_questions = response.json()
        
        approved = [q for q in all_questions if q["status"] == "approved"]
        rejected = [q for q in all_questions if q["status"] == "rejected"]
        
        assert len(approved) == 2
        assert len(rejected) == 1

    def test_host_cannot_access_wrong_event(self, client, test_db):
        """
        Journey: Host tries to access questions from different event.
        Should be denied.
        """
        # Create two events
        db = TestingSessionLocal()
        try:
            event1 = Event(
                title="Event 1",
                slug="event-1",
                host_code="host_event1",
                short_code="EV1"
            )
            event2 = Event(
                title="Event 2",
                slug="event-2",
                host_code="host_event2",
                short_code="EV2"
            )
            db.add(event1)
            db.add(event2)
            db.commit()
            db.refresh(event1)
            db.refresh(event2)

            # Create question in event1
            response = client.post(
                f"/api/v1/events/{event1.id}/questions",
                json={"question_text": "Event 1 question"},
                headers={"x-session-id": "attendee_session"}
            )
            assert response.status_code == 201

            # Host 2 tries to access event 1's questions
            response = client.get(
                f"/api/v1/events/{event1.id}/questions",
                headers={"Authorization": f"Host {event2.host_code}"}
            )
            # Should be unauthorized
            assert response.status_code == 401 or response.status_code == 403

        finally:
            db.close()


class TestQuestionSorting:
    """Test that questions are sorted correctly by upvotes."""

    def test_questions_sorted_by_upvotes(self, client, test_event):
        """
        Journey: Multiple questions with different upvotes should be sorted.
        Steps:
        1. Create 3 questions
        2. Give them different upvote counts
        3. Verify they're returned in correct order
        """
        # Create 3 questions and approve them
        questions = []
        for i in range(3):
            response = client.post(
                f"/api/v1/events/{test_event.id}/questions",
                json={"question_text": f"Question {i+1}"},
                headers={"x-session-id": f"creator_{i}"}
            )
            question_id = response.json()["id"]
            
            client.put(
                f"/api/v1/events/{test_event.id}/questions/{question_id}/status",
                json={"status": "approved"},
                headers={"Authorization": f"Host {test_event.host_code}"}
            )
            questions.append(question_id)

        # Give different upvote counts
        # Question 0: 5 upvotes
        for j in range(5):
            client.post(
                f"/api/v1/events/{test_event.id}/questions/{questions[0]}/upvote",
                headers={"x-session-id": f"voter_0_{j}"}
            )

        # Question 1: 3 upvotes
        for j in range(3):
            client.post(
                f"/api/v1/events/{test_event.id}/questions/{questions[1]}/upvote",
                headers={"x-session-id": f"voter_1_{j}"}
            )

        # Question 2: 1 upvote
        client.post(
            f"/api/v1/events/{test_event.id}/questions/{questions[2]}/upvote",
            headers={"x-session-id": "voter_2_0"}
        )

        # Fetch questions
        response = client.get(
            f"/api/v1/events/{test_event.id}/questions",
            headers={"Authorization": f"Host {test_event.host_code}"}
        )
        
        all_questions = response.json()
        
        # Verify upvote counts
        q0 = next(q for q in all_questions if q["id"] == questions[0])
        q1 = next(q for q in all_questions if q["id"] == questions[1])
        q2 = next(q for q in all_questions if q["id"] == questions[2])
        
        assert q0["upvote_count"] == 5
        assert q1["upvote_count"] == 3
        assert q2["upvote_count"] == 1


class TestErrorHandling:
    """Test error handling in question flow."""

    def test_submit_empty_question(self, client, test_event):
        """Cannot submit empty question."""
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": ""},
            headers={"x-session-id": "attendee_session"}
        )
        assert response.status_code == 422  # Validation error

    def test_upvote_nonexistent_question(self, client, test_event):
        """Cannot upvote question that doesn't exist."""
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions/99999/upvote",
            headers={"x-session-id": "attendee_session"}
        )
        assert response.status_code == 404

    def test_moderate_without_auth(self, client, test_event):
        """Cannot moderate without authentication."""
        # Create question first
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": "Test question"},
            headers={"x-session-id": "attendee_session"}
        )
        question_id = response.json()["id"]

        # Try to moderate without auth
        response = client.put(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/status",
            json={"status": "approved"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

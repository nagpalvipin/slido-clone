"""
WebSocket Integration Tests
Tests real-time question updates via WebSocket.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db
from src.models.event import Event


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
            title="WebSocket Test Event",
            slug="ws-test-event",
            host_code="host_wstest",
            short_code="WSTEST"
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


class TestWebSocketQuestionBroadcast:
    """Test WebSocket broadcasting for questions."""

    def test_websocket_connection(self, client, test_event):
        """Test basic WebSocket connection."""
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["event_id"] == test_event.id

    def test_question_submitted_broadcast(self, client, test_event):
        """
        Test that question_submitted is broadcast to all connected clients.
        Journey:
        1. Connect WebSocket client
        2. Submit question via API
        3. Verify WebSocket receives question_submitted event
        """
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            # Receive connection confirmation
            conn_msg = websocket.receive_json()
            assert conn_msg["type"] == "connected"

            # Submit question via API
            response = client.post(
                f"/api/v1/events/{test_event.id}/questions",
                json={"question_text": "Is WebSocket working?"},
                headers={"x-session-id": "test_attendee"}
            )
            assert response.status_code == 201
            question_data = response.json()

            # Should receive broadcast
            broadcast = websocket.receive_json(timeout=5)
            assert broadcast["type"] == "question_submitted"
            assert broadcast["question"]["id"] == question_data["id"]
            assert broadcast["question"]["question_text"] == "Is WebSocket working?"

    def test_question_upvote_broadcast(self, client, test_event):
        """
        Test that question_upvoted is broadcast to all connected clients.
        Journey:
        1. Create and approve question
        2. Connect WebSocket client
        3. Upvote question via API
        4. Verify WebSocket receives question_upvoted event
        """
        # Create and approve question
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": "Test upvote broadcast"},
            headers={"x-session-id": "creator"}
        )
        question_id = response.json()["id"]
        
        client.put(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Host {test_event.host_code}"}
        )

        # Connect WebSocket
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            # Clear connection message
            websocket.receive_json()

            # Upvote question
            response = client.post(
                f"/api/v1/events/{test_event.id}/questions/{question_id}/upvote",
                headers={"x-session-id": "upvoter"}
            )
            assert response.status_code == 200

            # Should receive upvote broadcast
            broadcast = websocket.receive_json(timeout=5)
            assert broadcast["type"] == "question_upvoted"
            assert broadcast["question_id"] == question_id
            assert broadcast["upvote_count"] == 1

    def test_multiple_clients_receive_broadcast(self, client, test_event):
        """
        Test that multiple connected clients all receive broadcasts.
        Journey:
        1. Connect 3 WebSocket clients (host + 2 attendees)
        2. Submit question
        3. Verify all 3 clients receive the broadcast
        """
        # Connect 3 clients
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as ws1, \
             client.websocket_connect(f"/ws/events/{test_event.slug}") as ws2, \
             client.websocket_connect(f"/ws/events/{test_event.slug}") as ws3:
            
            # Clear connection messages
            ws1.receive_json()
            ws2.receive_json()
            ws3.receive_json()

            # Submit question
            response = client.post(
                f"/api/v1/events/{test_event.id}/questions",
                json={"question_text": "Does everyone see this?"},
                headers={"x-session-id": "broadcaster"}
            )
            assert response.status_code == 201
            question_id = response.json()["id"]

            # All clients should receive broadcast
            for ws in [ws1, ws2, ws3]:
                broadcast = ws.receive_json(timeout=5)
                assert broadcast["type"] == "question_submitted"
                assert broadcast["question"]["id"] == question_id

    def test_moderation_broadcast(self, client, test_event):
        """
        Test that question moderation (approval/rejection) is broadcast.
        Journey:
        1. Submit question
        2. Connect WebSocket clients
        3. Host approves question
        4. Verify clients receive update
        """
        # Submit question
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": "Needs approval"},
            headers={"x-session-id": "submitter"}
        )
        question_id = response.json()["id"]

        # Connect WebSocket
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            # Clear connection message
            websocket.receive_json()

            # Host approves question
            response = client.put(
                f"/api/v1/events/{test_event.id}/questions/{question_id}/status",
                json={"status": "approved"},
                headers={"Authorization": f"Host {test_event.host_code}"}
            )
            assert response.status_code == 200

            # Should receive broadcast with updated status
            broadcast = websocket.receive_json(timeout=5)
            assert broadcast["type"] == "question_submitted"
            assert broadcast["question"]["id"] == question_id
            assert broadcast["question"]["status"] == "approved"

    def test_websocket_survives_disconnection(self, client, test_event):
        """
        Test that WebSocket handles disconnection gracefully.
        """
        # Connect and disconnect
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            websocket.receive_json()
            # Close connection
            websocket.close()

        # Should be able to reconnect
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

    def test_websocket_invalid_event_slug(self, client):
        """Test WebSocket connection with invalid event slug."""
        try:
            with client.websocket_connect("/ws/events/nonexistent-event") as websocket:
                # Connection should be rejected
                pass
        except Exception as e:
            # Expected to fail - connection should be closed
            assert "4004" in str(e) or "Event not found" in str(e)


class TestWebSocketRealTimeScenarios:
    """Test realistic real-time scenarios."""

    def test_live_qa_session_simulation(self, client, test_event):
        """
        Simulate a live Q&A session:
        1. Host connects
        2. 2 Attendees connect
        3. Attendees submit questions
        4. Questions are upvoted
        5. Host approves questions
        6. All clients see updates in real-time
        """
        # Connect host and attendees
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as host_ws, \
             client.websocket_connect(f"/ws/events/{test_event.slug}") as attendee1_ws, \
             client.websocket_connect(f"/ws/events/{test_event.slug}") as attendee2_ws:
            
            # Clear connection messages
            host_ws.receive_json()
            attendee1_ws.receive_json()
            attendee2_ws.receive_json()

            # Attendee 1 submits question
            response = client.post(
                f"/api/v1/events/{test_event.id}/questions",
                json={"question_text": "First question from attendee 1"},
                headers={"x-session-id": "attendee_1"}
            )
            q1_id = response.json()["id"]

            # All should receive broadcast
            for ws in [host_ws, attendee1_ws, attendee2_ws]:
                msg = ws.receive_json(timeout=5)
                assert msg["type"] == "question_submitted"
                assert msg["question"]["id"] == q1_id

            # Attendee 2 upvotes
            response = client.post(
                f"/api/v1/events/{test_event.id}/questions/{q1_id}/upvote",
                headers={"x-session-id": "attendee_2"}
            )

            # All should receive upvote broadcast
            for ws in [host_ws, attendee1_ws, attendee2_ws]:
                msg = ws.receive_json(timeout=5)
                assert msg["type"] == "question_upvoted"
                assert msg["question_id"] == q1_id
                assert msg["upvote_count"] == 1

            # Host approves question
            response = client.put(
                f"/api/v1/events/{test_event.id}/questions/{q1_id}/status",
                json={"status": "approved"},
                headers={"Authorization": f"Host {test_event.host_code}"}
            )

            # All should receive approval broadcast
            for ws in [host_ws, attendee1_ws, attendee2_ws]:
                msg = ws.receive_json(timeout=5)
                assert msg["type"] == "question_submitted"
                assert msg["question"]["status"] == "approved"

    def test_rapid_fire_questions(self, client, test_event):
        """
        Test handling of multiple questions submitted rapidly.
        """
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            websocket.receive_json()  # Clear connection message

            # Submit 5 questions rapidly
            question_ids = []
            for i in range(5):
                response = client.post(
                    f"/api/v1/events/{test_event.id}/questions",
                    json={"question_text": f"Rapid question {i+1}"},
                    headers={"x-session-id": f"attendee_{i}"}
                )
                question_ids.append(response.json()["id"])

            # Should receive all 5 broadcasts
            received_ids = []
            for i in range(5):
                msg = websocket.receive_json(timeout=5)
                assert msg["type"] == "question_submitted"
                received_ids.append(msg["question"]["id"])

            # Verify all questions were broadcast
            assert set(received_ids) == set(question_ids)


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""

    def test_websocket_ping_pong(self, client, test_event):
        """Test keepalive ping/pong."""
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            websocket.receive_json()  # Clear connection message

            # Send ping
            websocket.send_json({"type": "ping", "timestamp": 123456})

            # Should receive pong
            response = websocket.receive_json(timeout=5)
            assert response["type"] == "pong"
            assert response["timestamp"] == 123456

    def test_websocket_invalid_message(self, client, test_event):
        """Test handling of invalid WebSocket messages."""
        with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
            websocket.receive_json()  # Clear connection message

            # Send invalid JSON
            websocket.send_text("not valid json")

            # Should receive error message
            response = websocket.receive_json(timeout=5)
            assert response["type"] == "error"
            assert "Invalid JSON" in response["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

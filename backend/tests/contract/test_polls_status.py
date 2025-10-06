"""
Contract tests for PUT /api/v1/events/{event_id}/polls/{poll_id}/status endpoint.

These tests MUST FAIL initially to enforce TDD approach.
Tests verify the poll status management API contract.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


class TestPollsStatusContract:
    """Contract tests for poll status updates."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_event_and_poll(self, client):
        """Create event and poll for testing."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # Create event
        event_data = {
            "title": f"Status Test Event {unique_id}",
            "slug": f"status-test-{unique_id}",
            "description": f"Event for status testing - {unique_id}"
        }
        event_response = client.post("/api/v1/events", json=event_data)
        assert event_response.status_code == 201
        event = event_response.json()
        
        # Create poll
        poll_data = {
            "question_text": "Status Test Poll",
            "poll_type": "single",
            "options": [
                {"option_text": "Option A", "position": 0},
                {"option_text": "Option B", "position": 1}
            ]
        }
        headers = {"Authorization": f"Host {event['host_code']}"}
        poll_response = client.post(
            f"/api/v1/events/{event['id']}/polls",
            json=poll_data,
            headers=headers
        )
        assert poll_response.status_code == 201
        poll = poll_response.json()
        
        return {"event": event, "poll": poll}

    def test_update_poll_status_success(self, client, sample_event_and_poll):
        """Test successful poll status update."""
        event = sample_event_and_poll["event"]
        poll = sample_event_and_poll["poll"]
        
        response = client.put(
            f"/api/v1/events/{event['id']}/polls/{poll['id']}/status",
            json={"status": "active"},
            headers={"Authorization": f"Host {event['host_code']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_update_poll_status_unauthorized(self, client):
        """Test poll status update without authorization."""
        response = client.put(
            "/api/v1/events/1/polls/1/status",
            json={"status": "active"}
        )
        
        assert response.status_code == 401
"""
Contract tests for POST /api/v1/events/{event_id}/po    def test_vote_succ    def test_vote_succe    def test_vote_success        event = sample_event_and_poll[\"event\"]
        poll = sample_event_and_poll[\"poll\"]
        
        # First activate the poll
        activate_response = client.put(
            f\"/api/v1/events/{event['id']}/polls/{poll['id']}/status\",
            json={\"status\": \"active\"},
            headers={\"Authorization\": f\"Host {event['host_code']}\"}
        )
        assert activate_response.status_code == 200
        
        # Get the first option ID from the poll
        option_id = poll[\"options\"][0][\"id\"], client, sample_event_and_poll):
        \"\"\"Test successful vote submission.\"\"\"
        event = sample_event_and_poll[\"event\"]
        poll = sample_event_and_poll[\"poll\"]
        
        # First activate the poll
        activate_response = client.put(
            f\"/api/v1/events/{event['id']}/polls/{poll['id']}/status\",
            json={\"status\": \"active\"},
            headers={\"Authorization\": f\"Host {event['host_code']}\"}
        )
        assert activate_response.status_code == 200
        
        # Get the first option ID from the poll
        option_id = poll[\"options\"][0][\"id\"]
        
        response = client.post(
            f\"/api/v1/events/{event['id']}/polls/{poll['id']}/vote\",
            json={\"option_id\": option_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert \"vote_recorded\" in data sample_event_and_poll):
        \"\"\"Test successful vote submission.\"\"\"
        event = sample_event_and_poll[\"event\"]
        poll = sample_event_and_poll[\"poll\"]
        
        # First activate the poll
        activate_response = client.put(
            f\"/api/v1/events/{event['id']}/polls/{poll['id']}/status\",
            json={\"status\": \"active\"},
            headers={\"Authorization\": f\"Host {event['host_code']}\"}
        )
        assert activate_response.status_code == 200
        
        # Get the first option ID from the poll
        option_id = poll[\"options\"][0][\"id\"]
        
        response = client.post(
            f\"/api/v1/events/{event['id']}/polls/{poll['id']}/vote\",
            json={\"option_id\": option_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert \"vote_recorded\" in data, sample_event_and_poll):
        \"\"\"Test successful vote submission.\"\"\"
        event = sample_event_and_poll[\"event\"]
        poll = sample_event_and_poll[\"poll\"]
        
        # First activate the poll
        activate_response = client.put(
            f\"/api/v1/events/{event['id']}/polls/{poll['id']}/status\",
            json={\"status\": \"active\"},
            headers={\"Authorization\": f\"Host {event['host_code']}\"}
        )
        assert activate_response.status_code == 200
        
        # Get the first option ID from the poll
        option_id = poll[\"options\"][0][\"id\"]
        
        response = client.post(
            f\"/api/v1/events/{event['id']}/polls/{poll['id']}/vote\",
            json={\"option_id\": option_id}
        )
        
        assert response.status_code == 200
        data = response.json()ote endpoint.

These tests MUST FAIL initially to enforce TDD approach.
Tests verify the voting API contract against spec.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


class TestPollsVoteContract:
    """Contract tests for poll voting."""

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
            "title": f"Vote Test Event {unique_id}",
            "slug": f"vote-test-{unique_id}",
            "description": f"Event for vote testing - {unique_id}"
        }
        event_response = client.post("/api/v1/events", json=event_data)
        assert event_response.status_code == 201
        event = event_response.json()
        
        # Create poll
        poll_data = {
            "question_text": "Vote Test Poll",
            "poll_type": "single",
            "options": [
                {"option_text": "Vote Option A", "position": 0},
                {"option_text": "Vote Option B", "position": 1}
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

    def test_vote_success(self, client, sample_event_and_poll):
        """Test successful vote submission."""
        event = sample_event_and_poll["event"]
        poll = sample_event_and_poll["poll"]
        
        # Get the first option ID from the poll
        option_id = poll["options"][0]["id"]
        
        response = client.post(
            f"/api/v1/events/{event['id']}/polls/{poll['id']}/vote",
            json={"option_id": option_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "vote_recorded" in data

    def test_vote_poll_not_active(self, client):
        """Test voting on inactive poll."""
        response = client.post(
            "/api/v1/events/1/polls/1/vote",
            json={"option_id": 1}
        )
        
        # Should fail because poll is not active
        assert response.status_code == 400
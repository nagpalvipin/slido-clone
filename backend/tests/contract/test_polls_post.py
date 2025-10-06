"""
Contract tests for POST /api/v1/events/{event_id}/polls endpoint.

These tests MUST FAIL initially to enforce TDD approach.
Tests verify the polls creation API contract against spec.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


class TestPollsPostContract:
    """Contract tests for creating polls."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_event(self, client):
        """Create a sample event for testing."""
        event_data = {
            "title": "Poll Test Workshop",
            "slug": "poll-workshop",
            "description": "Workshop for poll testing"
        }
        response = client.post("/api/v1/events", json=event_data)
        return response.json()

    def test_create_poll_success(self, client, sample_event):
        """Test successful poll creation with valid data."""
        # Given: Valid poll data and host authentication
        poll_data = {
            "question_text": "Which topic should we cover next?",
            "poll_type": "single",
            "options": [
                {"option_text": "Async/Await Patterns", "position": 0},
                {"option_text": "Error Handling", "position": 1},
                {"option_text": "Performance Optimization", "position": 2},
                {"option_text": "Testing Strategies", "position": 3}
            ]
        }
        headers = {"Authorization": f"Host {sample_event['host_code']}"}

        # When: Creating a poll
        response = client.post(
            f"/api/v1/events/{sample_event['id']}/polls",
            json=poll_data,
            headers=headers
        )

        # Then: Poll is created successfully
        assert response.status_code == 201
        
        # Verify response structure matches contract
        data = response.json()
        assert "id" in data
        assert data["question_text"] == "Which topic should we cover next?"
        assert data["poll_type"] == "single"
        assert data["status"] == "draft"
        assert "created_at" in data
        
        # Verify options structure
        assert "options" in data
        options = data["options"]
        assert len(options) == 4
        
        for i, option in enumerate(options):
            assert "id" in option
            assert option["position"] == i
            assert option["vote_count"] == 0
            assert option["option_text"] == poll_data["options"][i]["option_text"]

    def test_create_poll_unauthorized(self, client, sample_event):
        """Test poll creation without host authentication."""
        poll_data = {
            "question_text": "Test Question",
            "poll_type": "single",
            "options": [
                {"option_text": "Option 1", "position": 0},
                {"option_text": "Option 2", "position": 1}
            ]
        }

        # When: Creating poll without authentication
        response = client.post(
            f"/api/v1/events/{sample_event['id']}/polls",
            json=poll_data
        )

        # Then: Unauthorized error is returned
        assert response.status_code == 401

    def test_create_poll_invalid_host_code(self, client, sample_event):
        """Test poll creation with invalid host code."""
        poll_data = {
            "question_text": "Test Question",
            "poll_type": "single",
            "options": [
                {"option_text": "Option 1", "position": 0}
            ]
        }
        headers = {"Authorization": "Host invalid_code"}

        # When: Creating poll with invalid host code
        response = client.post(
            f"/api/v1/events/{sample_event['id']}/polls",
            json=poll_data,
            headers=headers
        )

        # Then: Unauthorized error is returned
        assert response.status_code == 401

    def test_create_poll_validation_errors(self, client, sample_event):
        """Test validation errors for invalid poll data."""
        headers = {"Authorization": f"Host {sample_event['host_code']}"}

        # Test missing required fields
        response = client.post(
            f"/api/v1/events/{sample_event['id']}/polls",
            json={},
            headers=headers
        )
        assert response.status_code == 422

        # Test invalid poll_type
        response = client.post(
            f"/api/v1/events/{sample_event['id']}/polls",
            json={
                "question_text": "Test Question",
                "poll_type": "invalid_type",
                "options": [{"option_text": "Option 1", "position": 0}]
            },
            headers=headers
        )
        assert response.status_code == 422

    def test_create_poll_multiple_choice(self, client, sample_event):
        """Test creating multiple choice poll."""
        poll_data = {
            "question_text": "Select all that apply",
            "poll_type": "multiple",
            "options": [
                {"option_text": "Option A", "position": 0},
                {"option_text": "Option B", "position": 1},
                {"option_text": "Option C", "position": 2}
            ]
        }
        headers = {"Authorization": f"Host {sample_event['host_code']}"}

        response = client.post(
            f"/api/v1/events/{sample_event['id']}/polls",
            json=poll_data,
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["poll_type"] == "multiple"

    def test_create_poll_event_not_found(self, client, sample_event):
        """Test poll creation for non-existent event."""
        poll_data = {
            "question_text": "Test Question",
            "poll_type": "single",
            "options": [{"option_text": "Option 1", "position": 0}]
        }
        headers = {"Authorization": f"Host {sample_event['host_code']}"}

        response = client.post(
            "/api/v1/events/999999/polls",
            json=poll_data,
            headers=headers
        )

        assert response.status_code == 404
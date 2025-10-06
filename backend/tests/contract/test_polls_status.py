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

    def test_update_poll_status_success(self, client):
        """Test successful poll status update."""
        # This test will fail initially - no implementation yet
        response = client.put(
            "/api/v1/events/1/polls/1/status",
            json={"status": "active"},
            headers={"Authorization": "Host host_code"}
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
"""
Contract tests for POST /api/v1/events/{event_id}/polls/{poll_id}/vote endpoint.

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

    def test_vote_success(self, client):
        """Test successful vote submission."""
        # This test will fail initially - no implementation yet
        response = client.post(
            "/api/v1/events/1/polls/1/vote",
            json={"option_id": 1}
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
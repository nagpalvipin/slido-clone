"""
Contract tests for GET /api/v1/events/{slug}/host endpoint.

These tests MUST FAIL initially to enforce TDD approach.
Tests verify the host view API contract against spec.
"""

import pytest


class TestEventsHostContract:
    """Contract tests for host event view."""

    @pytest.fixture
    def sample_event(self, client, sample_event_data):
        """Create a sample event for testing."""
        response = client.post("/api/v1/events", json=sample_event_data)
        return response.json()

    def test_get_host_view_success(self, client, sample_event):
        """Test successful host view retrieval with valid host code."""
        # When: Accessing host view with valid host code
        headers = {"Authorization": f"Host {sample_event['host_code']}"}
        response = client.get(
            f"/api/v1/events/{sample_event['slug']}/host",
            headers=headers
        )

        # Then: Full host view is returned
        assert response.status_code == 200

        # Verify response includes host-only fields
        data = response.json()
        assert data["id"] == sample_event["id"]
        assert data["title"] == sample_event["title"]
        assert data["slug"] == sample_event["slug"]
        assert data["short_code"] == sample_event["short_code"]
        assert data["host_code"] == sample_event["host_code"]
        assert "created_at" in data
        assert "attendee_count" in data

        # Verify polls and questions arrays exist
        assert "polls" in data
        assert "questions" in data
        assert isinstance(data["polls"], list)
        assert isinstance(data["questions"], list)

    def test_get_host_view_invalid_host_code(self, client, sample_event):
        """Test host view access with invalid host code."""
        # When: Using invalid host code
        headers = {"Authorization": "Host invalid_host_code"}
        response = client.get(
            f"/api/v1/events/{sample_event['slug']}/host",
            headers=headers
        )

        # Then: Unauthorized error is returned
        assert response.status_code == 401
        assert "invalid host code" in response.json()["detail"].lower()

    def test_get_host_view_missing_auth(self, client, sample_event):
        """Test host view access without authentication."""
        # When: Accessing host view without auth header
        response = client.get(f"/api/v1/events/{sample_event['slug']}/host")

        # Then: Unauthorized error is returned
        assert response.status_code == 401

    def test_get_host_view_malformed_auth(self, client, sample_event):
        """Test host view access with malformed auth header."""
        # When: Using malformed auth header
        headers = {"Authorization": "Bearer token123"}  # Wrong format
        response = client.get(
            f"/api/v1/events/{sample_event['slug']}/host",
            headers=headers
        )

        # Then: Unauthorized error is returned
        assert response.status_code == 401

    def test_get_host_view_event_not_found(self, client, sample_event):
        """Test host view for non-existent event."""
        # When: Accessing non-existent event with valid host code
        headers = {"Authorization": f"Host {sample_event['host_code']}"}
        response = client.get(
            "/api/v1/events/non-existent/host",
            headers=headers
        )

        # Then: Not found error is returned
        assert response.status_code == 404

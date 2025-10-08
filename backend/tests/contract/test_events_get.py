"""
Contract tests for GET /api/v1/events/{slug} endpoint.

These tests MUST FAIL initially to enforce TDD approach.
Tests verify the events retrieval API contract against spec.
"""

import pytest


class TestEventsGetContract:
    """Contract tests for retrieving events by slug."""

    @pytest.fixture
    def sample_event(self, client, sample_event_data):
        """Create a sample event for testing."""
        response = client.post("/api/v1/events", json=sample_event_data)
        return response.json()

    def test_get_event_success(self, client, sample_event):
        """Test successful event retrieval with valid slug."""
        # When: Retrieving an existing event by slug
        response = client.get(f"/api/v1/events/{sample_event['slug']}")

        # Then: Event details are returned
        assert response.status_code == 200

        # Verify response structure matches contract (attendee view)
        data = response.json()
        assert data["id"] == sample_event["id"]
        assert data["title"] == sample_event["title"]
        assert data["slug"] == sample_event["slug"]
        assert data["description"] == sample_event["description"]
        assert data["is_active"] is True

        # Verify attendee view excludes sensitive fields
        assert "host_code" not in data
        assert "short_code" not in data  # Available in host view only

    def test_get_event_not_found(self, client):
        """Test retrieval of non-existent event."""
        # When: Retrieving a non-existent event
        response = client.get("/api/v1/events/non-existent-slug")

        # Then: 404 error is returned
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_inactive_event(self, client, sample_event):
        """Test retrieval of inactive event."""
        # Note: This test assumes we have a way to deactivate events
        # For now, just test that is_active field is properly returned
        response = client.get(f"/api/v1/events/{sample_event['slug']}")
        assert response.status_code == 200

        data = response.json()
        assert "is_active" in data
        assert isinstance(data["is_active"], bool)

    def test_get_event_slug_case_sensitivity(self, client, sample_event):
        """Test that slug matching is case-sensitive."""
        # When: Using different case for slug
        uppercase_slug = sample_event['slug'].upper()
        response = client.get(f"/api/v1/events/{uppercase_slug}")

        # Then: Should not find the event (case-sensitive)
        assert response.status_code == 404

    def test_get_event_with_special_characters(self, client):
        """Test event retrieval with special characters in slug."""
        # Create event with hyphens in slug
        event_data = {
            "title": "Special Event",
            "slug": "special-event-with-hyphens"
        }
        response = client.post("/api/v1/events", json=event_data)
        created_event = response.json()

        # Retrieve the event
        response = client.get(f"/api/v1/events/{created_event['slug']}")
        assert response.status_code == 200
        assert response.json()["slug"] == "special-event-with-hyphens"

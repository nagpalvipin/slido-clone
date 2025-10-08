"""
Contract tests for POST /api/v1/events with custom host code.

Tests based on contracts/create-event-custom-host-code.md
These tests define the expected behavior - implementation will make them pass.
"""

import pytest

from src.main import app


@pytest.mark.contract
class TestCreateEventCustomHostCode:
    """Contract tests for event creation with custom host codes."""

    def test_create_event_with_custom_host_code(self, client):
        """
        Test creating event with valid custom host code.

        Expected: 201 Created with custom host code in response
        """
        response = client.post("/api/v1/events", json={
            "title": "Test Event with Custom Code",
            "slug": "test-event-custom-123",
            "description": "Test description",
            "host_code": "host_test12345678"  # host_ + 12 chars = 17 total
        })

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["host_code"] == "host_test12345678"
        assert data["title"] == "Test Event with Custom Code"
        assert data["slug"] == "test-event-custom-123"
        assert "short_code" in data
        assert data["is_active"] is True
        assert data["id"] is not None
        assert "created_at" in data

    def test_create_event_auto_generate_host_code(self, client):
        """
        Test creating event without host code - should auto-generate.

        Expected: 201 Created with auto-generated host code (host_[a-z0-9]{12})
        """
        response = client.post("/api/v1/events", json={
            "title": "Test Event Auto Generate",
            "slug": "test-event-auto-456"
        })

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["host_code"].startswith("host_"), f"Host code should start with 'host_': {data['host_code']}"
        assert len(data["host_code"]) == 17, f"Host code should be 17 chars: {data['host_code']}"

        # Verify format: host_[a-z0-9]{12}
        import re
        pattern = re.compile(r'^host_[a-z0-9]{12}$')
        assert pattern.match(data["host_code"]), f"Invalid host code format: {data['host_code']}"

    def test_create_event_duplicate_host_code(self, client):
        """
        Test creating event with duplicate host code.

        Expected: 409 Conflict with error message
        """
        # Create first event
        first_response = client.post("/api/v1/events", json={
            "title": "First Event",
            "slug": "first-event-789",
            "host_code": "host_dup123456789"  # host_ + 12 chars
        })
        assert first_response.status_code == 201, f"First event creation should succeed: {first_response.text}"

        # Attempt duplicate host code with different slug
        duplicate_response = client.post("/api/v1/events", json={
            "title": "Second Event",
            "slug": "second-event-789",
            "host_code": "host_dup123456789"
        })

        assert duplicate_response.status_code == 409, f"Expected 409, got {duplicate_response.status_code}"
        error_detail = duplicate_response.json()["detail"]
        assert "already in use" in error_detail.lower() or "duplicate" in error_detail.lower(), \
            f"Error message should mention duplicate/already in use: {error_detail}"

    def test_create_event_invalid_host_code_format(self, client):
        """
        Test creating event with invalid host code format.

        Expected: 422 Unprocessable Entity with format error
        """
        invalid_codes = [
            ("invalid-code", "test-invalid-1"),      # Wrong prefix
            ("host_SHORT", "test-invalid-2"),        # Too short (9 chars not 12)
            ("host_ABC123def", "test-invalid-3"),    # Uppercase + wrong length
            ("mycode123456789", "test-invalid-4"),   # No host_ prefix
            ("host_with_under", "test-invalid-5"),   # Underscores (only alphanumeric allowed)
        ]

        for invalid_code, slug in invalid_codes:
            response = client.post("/api/v1/events", json={
                "title": "Test Event",
                "slug": slug,
                "host_code": invalid_code
            })

            assert response.status_code in [422, 400], \
                f"Expected 422 or 400 for invalid code '{invalid_code}', got {response.status_code}: {response.text}"

            if response.status_code == 422:
                error_detail = response.json()["detail"]
                assert "format" in error_detail.lower() or "invalid" in error_detail.lower() or "pattern" in error_detail.lower(), \
                    f"Error message should mention format/invalid/pattern for '{invalid_code}': {error_detail}"

    def test_create_event_host_code_case_insensitivity(self, client):
        """
        Test that host codes are case-insensitive (normalized to lowercase).

        Expected: Uppercase/mixed case codes normalized, duplicates detected
        """
        # Create event with lowercase host code
        first_response = client.post("/api/v1/events", json={
            "title": "First Event",
            "slug": "first-event-case",
            "host_code": "host_case12345678"  # host_ + 12 chars
        })
        assert first_response.status_code == 201

        # Try to create with uppercase version - should conflict
        uppercase_response = client.post("/api/v1/events", json={
            "title": "Second Event",
            "slug": "second-event-case",
            "host_code": "HOST_CASE12345678"  # Same but uppercase
        })

        # Should be 409 Conflict (duplicate) after normalization
        assert uppercase_response.status_code == 409, \
            f"Expected 409 for duplicate (case-insensitive), got {uppercase_response.status_code}"

    def test_create_event_missing_required_fields(self, client):
        """
        Test creating event without required fields (title, slug).

        Expected: 400 or 422 validation error
        """
        # Missing title
        response_no_title = client.post("/api/v1/events", json={
            "slug": "test-no-title"
        })
        assert response_no_title.status_code in [400, 422], \
            f"Expected 400/422 for missing title, got {response_no_title.status_code}"

        # Missing slug
        response_no_slug = client.post("/api/v1/events", json={
            "title": "Test No Slug"
        })
        assert response_no_slug.status_code in [400, 422], \
            f"Expected 400/422 for missing slug, got {response_no_slug.status_code}"

    def test_create_event_with_description(self, client):
        """
        Test creating event with optional description field.

        Expected: 201 Created with description in response
        """
        description_text = "This is a detailed event description for testing purposes"
        response = client.post("/api/v1/events", json={
            "title": "Event with Description",
            "slug": "event-with-desc",
            "description": description_text,
            "host_code": "host_desc12345678"  # host_ + 12 chars
        })

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["description"] == description_text


@pytest.fixture
def client(test_db):
    """Create test client with database override."""
    from fastapi.testclient import TestClient
    return TestClient(app)

"""
Contract tests for POST /api/v1/events endpoint.

These tests MUST FAIL initially to enforce TDD approach.
Tests verify the events creation API contract against spec.
"""



class TestEventsPostContract:
    """Contract tests for creating events."""

    def test_create_event_success(self, client):
        """Test successful event creation with valid data."""
        # Given: Valid event data
        event_data = {
            "title": "Advanced JavaScript Workshop",
            "slug": "js-advanced-2025",
            "description": "Deep dive into async patterns and modern JS"
        }

        # When: Creating an event
        response = client.post("/api/v1/events", json=event_data)

        # Then: Event is created successfully
        assert response.status_code == 201

        # Verify response structure matches contract
        data = response.json()
        assert "id" in data
        assert data["title"] == "Advanced JavaScript Workshop"
        assert data["slug"] == "js-advanced-2025"
        assert "short_code" in data
        assert "host_code" in data
        assert data["description"] == "Deep dive into async patterns and modern JS"
        assert "created_at" in data
        assert data["is_active"] is True
        assert data["attendee_count"] == 0

        # Verify generated codes format
        assert len(data["short_code"]) == 8  # ABC12345 format
        assert data["host_code"].startswith("host_")
        assert len(data["host_code"]) == 17  # host_ + 12 chars

    def test_create_event_validation_errors(self, client):
        """Test validation errors for invalid event data."""
        # Test missing required fields
        response = client.post("/api/v1/events", json={})
        assert response.status_code == 422

        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]
        assert "title" in error_fields
        assert "slug" in error_fields

    def test_create_event_title_validation(self, client):
        """Test title validation rules."""
        # Title too long (>200 chars)
        long_title = "x" * 201
        response = client.post("/api/v1/events", json={
            "title": long_title,
            "slug": "test-event"
        })
        assert response.status_code == 422

        # Title too short (empty)
        response = client.post("/api/v1/events", json={
            "title": "",
            "slug": "test-event"
        })
        assert response.status_code == 422

    def test_create_event_slug_validation(self, client):
        """Test slug validation rules."""
        # Slug too short (<3 chars)
        response = client.post("/api/v1/events", json={
            "title": "Test Event",
            "slug": "ab"
        })
        assert response.status_code == 422

        # Slug too long (>50 chars)
        long_slug = "x" * 51
        response = client.post("/api/v1/events", json={
            "title": "Test Event",
            "slug": long_slug
        })
        assert response.status_code == 422

        # Invalid slug characters
        response = client.post("/api/v1/events", json={
            "title": "Test Event",
            "slug": "invalid slug!"
        })
        assert response.status_code == 422

    def test_create_event_description_validation(self, client):
        """Test description validation rules."""
        # Description too long (>1000 chars)
        long_description = "x" * 1001
        response = client.post("/api/v1/events", json={
            "title": "Test Event",
            "slug": "test-event",
            "description": long_description
        })
        assert response.status_code == 422

        # Description is optional - should work without it
        response = client.post("/api/v1/events", json={
            "title": "Test Event",
            "slug": "test-event-no-desc"
        })
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_event_duplicate_slug(self, client):
        """Test that duplicate slugs are rejected."""
        # Create first event
        event_data = {
            "title": "First Event",
            "slug": "unique-slug"
        }
        response = client.post("/api/v1/events", json=event_data)
        assert response.status_code == 201

        # Try to create second event with same slug
        duplicate_data = {
            "title": "Second Event",
            "slug": "unique-slug"
        }
        response = client.post("/api/v1/events", json=duplicate_data)
        assert response.status_code == 409  # Conflict
        assert "slug already exists" in response.json()["detail"].lower()

"""
Integration tests for complete host workflow.

These tests MUST FAIL initially to enforce TDD approach.
Tests verify end-to-end host scenarios across multiple endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


class TestHostWorkflowIntegration:
    """Integration tests for complete host workflows."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    def test_complete_host_event_lifecycle(self, client):
        """Test complete host workflow from event creation to poll management."""
        # Step 1: Host creates an event
        event_data = {
            "title": "Complete Workshop Integration",
            "slug": "complete-workshop",
            "description": "Full integration test workshop"
        }
        
        event_response = client.post("/api/v1/events", json=event_data)
        assert event_response.status_code == 201
        event = event_response.json()
        
        # Step 2: Host accesses their event dashboard
        headers = {"Authorization": f"Host {event['host_code']}"}
        dashboard_response = client.get(
            f"/api/v1/events/{event['slug']}/host",
            headers=headers
        )
        assert dashboard_response.status_code == 200
        dashboard = dashboard_response.json()
        
        # Verify initial state
        assert len(dashboard["polls"]) == 0
        assert len(dashboard["questions"]) == 0
        assert dashboard["attendee_count"] == 0

        # Step 3: Host creates multiple polls
        poll1_data = {
            "question_text": "What's your experience level?",
            "poll_type": "single",
            "options": [
                {"option_text": "Beginner", "position": 0},
                {"option_text": "Intermediate", "position": 1},
                {"option_text": "Advanced", "position": 2}
            ]
        }
        
        poll1_response = client.post(
            f"/api/v1/events/{event['id']}/polls",
            json=poll1_data,
            headers=headers
        )
        assert poll1_response.status_code == 201
        poll1 = poll1_response.json()
        assert poll1["status"] == "draft"

        poll2_data = {
            "question_text": "Preferred learning format?",
            "poll_type": "multiple",
            "options": [
                {"option_text": "Live Demo", "position": 0},
                {"option_text": "Code Examples", "position": 1},
                {"option_text": "Discussion", "position": 2}
            ]
        }
        
        poll2_response = client.post(
            f"/api/v1/events/{event['id']}/polls",
            json=poll2_data,
            headers=headers
        )
        assert poll2_response.status_code == 201
        poll2 = poll2_response.json()

        # Step 4: Host activates first poll
        activate_response = client.put(
            f"/api/v1/events/{event['id']}/polls/{poll1['id']}/status",
            json={"status": "active"},
            headers=headers
        )
        assert activate_response.status_code == 200

        # Step 5: Verify updated dashboard state
        updated_dashboard = client.get(
            f"/api/v1/events/{event['slug']}/host",
            headers=headers
        ).json()
        
        assert len(updated_dashboard["polls"]) == 2
        active_polls = [p for p in updated_dashboard["polls"] if p["status"] == "active"]
        assert len(active_polls) == 1
        assert active_polls[0]["id"] == poll1["id"]

        # Step 6: Simulate attendee participation
        # Attendee views event
        attendee_response = client.get(f"/api/v1/events/{event['slug']}")
        assert attendee_response.status_code == 200

        # Attendee votes on active poll
        vote_response = client.post(
            f"/api/v1/events/{event['id']}/polls/{poll1['id']}/vote",
            json={"option_id": poll1["options"][1]["id"]}  # Vote for "Intermediate"
        )
        assert vote_response.status_code == 200

        # Step 7: Host closes poll and checks results
        close_response = client.put(
            f"/api/v1/events/{event['id']}/polls/{poll1['id']}/status",
            json={"status": "closed"},
            headers=headers
        )
        assert close_response.status_code == 200

        # Step 8: Verify final dashboard reflects vote
        final_dashboard = client.get(
            f"/api/v1/events/{event['slug']}/host",
            headers=headers
        ).json()
        
        closed_poll = next(p for p in final_dashboard["polls"] if p["id"] == poll1["id"])
        assert closed_poll["status"] == "closed"
        
        # Check vote was recorded
        intermediate_option = next(
            opt for opt in closed_poll["options"] 
            if opt["option_text"] == "Intermediate"
        )
        assert intermediate_option["vote_count"] == 1

    def test_host_poll_management_workflow(self, client):
        """Test comprehensive poll management workflow."""
        # Setup event
        event_response = client.post("/api/v1/events", json={
            "title": "Poll Management Test",
            "slug": "poll-mgmt-test"
        })
        event = event_response.json()
        headers = {"Authorization": f"Host {event['host_code']}"}

        # Create poll
        poll_response = client.post(
            f"/api/v1/events/{event['id']}/polls",
            json={
                "question_text": "Test Poll Management",
                "poll_type": "single",
                "options": [
                    {"option_text": "Yes", "position": 0},
                    {"option_text": "No", "position": 1}
                ]
            },
            headers=headers
        )
        poll = poll_response.json()

        # Test poll lifecycle: draft -> active -> closed
        statuses = ["active", "closed"]
        for status in statuses:
            response = client.put(
                f"/api/v1/events/{event['id']}/polls/{poll['id']}/status",
                json={"status": status},
                headers=headers
            )
            assert response.status_code == 200
            assert response.json()["status"] == status

    def test_host_error_handling_workflow(self, client):
        """Test host workflow error handling scenarios."""
        # Setup
        event_response = client.post("/api/v1/events", json={
            "title": "Error Test Event",
            "slug": "error-test"
        })
        event = event_response.json()
        headers = {"Authorization": f"Host {event['host_code']}"}

        # Test creating poll with invalid data
        invalid_poll = client.post(
            f"/api/v1/events/{event['id']}/polls",
            json={"question_text": ""},  # Invalid empty question
            headers=headers
        )
        assert invalid_poll.status_code == 422

        # Test accessing non-existent poll
        non_existent_poll = client.put(
            f"/api/v1/events/{event['id']}/polls/99999/status",
            json={"status": "active"},
            headers=headers
        )
        assert non_existent_poll.status_code == 404

        # Test wrong host code
        wrong_headers = {"Authorization": "Host wrong_code"}
        unauthorized = client.post(
            f"/api/v1/events/{event['id']}/polls",
            json={
                "question_text": "Unauthorized test",
                "poll_type": "single",
                "options": [{"option_text": "Test", "position": 0}]
            },
            headers=wrong_headers
        )
        assert unauthorized.status_code == 401
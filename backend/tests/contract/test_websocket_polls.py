"""
Contract tests for WebSocket real-time poll updates.

These tests MUST FAIL initially to enforce TDD approach.
Tests verify WebSocket real-time functionality for polls.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from src.main import app


class TestWebSocketPollsContract:
    """Contract tests for WebSocket poll updates."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_event(self, client):
        """Create a sample event for testing."""
        event_data = {
            "title": "WebSocket Poll Test",
            "slug": "websocket-test",
            "description": "Event for WebSocket testing"
        }
        response = client.post("/api/v1/events", json=event_data)
        return response.json()

    def test_websocket_connection_success(self, client, sample_event):
        """Test successful WebSocket connection to event room."""
        # When: Connecting to WebSocket for specific event
        with client.websocket_connect(f"/ws/events/{sample_event['slug']}") as websocket:
            # Then: Connection is established
            # Send join message
            websocket.send_json({
                "type": "join",
                "event_id": sample_event["id"]
            })
            
            # Should receive confirmation
            data = websocket.receive_json()
            assert data["type"] == "joined"
            assert data["event_id"] == sample_event["id"]

    def test_websocket_poll_created_broadcast(self, client, sample_event):
        """Test that poll creation is broadcast to connected clients."""
        # Given: WebSocket connection established
        with client.websocket_connect(f"/ws/events/{sample_event['slug']}") as websocket:
            websocket.send_json({
                "type": "join",
                "event_id": sample_event["id"]
            })
            websocket.receive_json()  # Join confirmation

            # When: Host creates a new poll
            poll_data = {
                "question_text": "Real-time poll question",
                "poll_type": "single",
                "options": [
                    {"option_text": "Option 1", "position": 0},
                    {"option_text": "Option 2", "position": 1}
                ]
            }
            headers = {"Authorization": f"Host {sample_event['host_code']}"}
            
            # Create poll via REST API
            response = client.post(
                f"/api/v1/events/{sample_event['id']}/polls",
                json=poll_data,
                headers=headers
            )
            assert response.status_code == 201

            # Then: WebSocket clients should receive poll_created event
            message = websocket.receive_json()
            assert message["type"] == "poll_created"
            assert "poll" in message
            assert message["poll"]["question_text"] == "Real-time poll question"

    def test_websocket_poll_status_update_broadcast(self, client, sample_event):
        """Test that poll status updates are broadcast in real-time."""
        # Given: Event with an existing poll
        poll_data = {
            "question_text": "Status update test",
            "poll_type": "single", 
            "options": [{"option_text": "Test Option", "position": 0}]
        }
        headers = {"Authorization": f"Host {sample_event['host_code']}"}
        
        poll_response = client.post(
            f"/api/v1/events/{sample_event['id']}/polls",
            json=poll_data,
            headers=headers
        )
        poll_id = poll_response.json()["id"]

        # Connect to WebSocket
        with client.websocket_connect(f"/ws/events/{sample_event['slug']}") as websocket:
            websocket.send_json({"type": "join", "event_id": sample_event["id"]})
            websocket.receive_json()  # Join confirmation
            websocket.receive_json()  # Poll created event

            # When: Poll status is updated to active
            status_response = client.put(
                f"/api/v1/events/{sample_event['id']}/polls/{poll_id}/status",
                json={"status": "active"},
                headers=headers
            )
            assert status_response.status_code == 200

            # Then: WebSocket clients receive poll_status_updated event
            message = websocket.receive_json()
            assert message["type"] == "poll_status_updated"
            assert message["poll_id"] == poll_id
            assert message["status"] == "active"

    def test_websocket_vote_update_broadcast(self, client, sample_event):
        """Test that vote updates are broadcast in real-time (<100ms requirement)."""
        import time
        
        # Given: Active poll
        poll_data = {
            "question_text": "Vote broadcast test",
            "poll_type": "single",
            "options": [
                {"option_text": "Option A", "position": 0},
                {"option_text": "Option B", "position": 1}
            ]
        }
        headers = {"Authorization": f"Host {sample_event['host_code']}"}
        
        poll_response = client.post(
            f"/api/v1/events/{sample_event['id']}/polls",
            json=poll_data,
            headers=headers
        )
        poll_data_response = poll_response.json()
        poll_id = poll_data_response["id"]
        option_id = poll_data_response["options"][0]["id"]

        # Activate poll
        client.put(
            f"/api/v1/events/{sample_event['id']}/polls/{poll_id}/status",
            json={"status": "active"},
            headers=headers
        )

        # Connect to WebSocket
        with client.websocket_connect(f"/ws/events/{sample_event['slug']}") as websocket:
            websocket.send_json({"type": "join", "event_id": sample_event["id"]})
            websocket.receive_json()  # Join confirmation
            
            # Clear any existing messages
            try:
                while True:
                    websocket.receive_json(timeout=0.1)
            except:
                pass

            # When: Attendee votes on the poll
            start_time = time.time()
            
            vote_response = client.post(
                f"/api/v1/events/{sample_event['id']}/polls/{poll_id}/vote",
                json={"option_id": option_id}
            )
            assert vote_response.status_code == 200

            # Then: Vote update is broadcast within 100ms (constitutional requirement)
            message = websocket.receive_json()
            end_time = time.time()
            
            broadcast_time_ms = (end_time - start_time) * 1000
            assert broadcast_time_ms < 100  # Constitutional <100ms requirement
            
            assert message["type"] == "vote_updated"
            assert message["poll_id"] == poll_id
            assert "results" in message

    def test_websocket_invalid_event(self, client):
        """Test WebSocket connection to non-existent event."""
        # When: Connecting to non-existent event
        with pytest.raises(Exception):  # Connection should fail
            with client.websocket_connect("/ws/events/non-existent-event"):
                pass

    def test_websocket_multiple_clients(self, client, sample_event):
        """Test that updates are broadcast to multiple connected clients."""
        # Given: Multiple WebSocket connections
        with client.websocket_connect(f"/ws/events/{sample_event['slug']}") as ws1:
            with client.websocket_connect(f"/ws/events/{sample_event['slug']}") as ws2:
                # Join both clients
                ws1.send_json({"type": "join", "event_id": sample_event["id"]})
                ws2.send_json({"type": "join", "event_id": sample_event["id"]})
                
                ws1.receive_json()  # Join confirmation
                ws2.receive_json()  # Join confirmation

                # When: Poll is created
                poll_data = {
                    "question_text": "Multi-client test",
                    "poll_type": "single",
                    "options": [{"option_text": "Test", "position": 0}]
                }
                headers = {"Authorization": f"Host {sample_event['host_code']}"}
                
                response = client.post(
                    f"/api/v1/events/{sample_event['id']}/polls",
                    json=poll_data,
                    headers=headers
                )
                assert response.status_code == 201

                # Then: Both clients receive the update
                msg1 = ws1.receive_json()
                msg2 = ws2.receive_json()
                
                assert msg1["type"] == "poll_created"
                assert msg2["type"] == "poll_created"
                assert msg1["poll"]["question_text"] == "Multi-client test"
                assert msg2["poll"]["question_text"] == "Multi-client test"
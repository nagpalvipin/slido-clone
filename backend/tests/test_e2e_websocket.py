"""
End-to-End WebSocket Tests
Tests actual WebSocket broadcasts during question flow.
"""

import pytest
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db
from src.models.event import Event


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_event():
    """Create a test event directly in the database."""
    db = TestingSessionLocal()
    try:
        event = Event(
            title="E2E Test Event",
            slug="e2e-test",
            host_code="host_e2etest",
            short_code="E2E"
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        yield event
    finally:
        db.close()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_question_submitted_broadcast_e2e(client, test_event):
    """
    CRITICAL TEST: Verify WebSocket broadcasts when question is submitted.
    
    This test simulates:
    1. Host opens dashboard (WebSocket connected)
    2. Attendee submits question via API
    3. Host should receive WebSocket broadcast immediately
    """
    messages_received = []
    
    print(f"\n🔧 Test event: id={test_event.id}, slug={test_event.slug}")
    
    # Connect WebSocket as "host"
    with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
        # Receive connection confirmation
        conn_msg = websocket.receive_json()
        assert conn_msg["type"] == "connected"
        print(f"✅ WebSocket connected: {conn_msg}")
        
        # Submit question via API (simulating attendee)
        print(f"\n📝 Submitting question for event_id={test_event.id}...")
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": "Does WebSocket broadcast work?"},
            headers={"x-session-id": "test_attendee_123"}
        )
        
        print(f"API Response: {response.status_code} - {response.json()}")
        assert response.status_code == 201, f"Failed to create question: {response.text}"
        question_data = response.json()
        
        # CRITICAL: Try to receive WebSocket message
        try:
            print("\n⏳ Waiting for WebSocket broadcast...")
            import select
            
            # Use select with timeout to check if message is available
            broadcast = websocket.receive_json()
            print(f"✅ Received broadcast: {broadcast}")
            messages_received.append(broadcast)
            
            # Verify broadcast content
            assert broadcast["type"] == "question_submitted", f"Wrong event type: {broadcast['type']}"
            assert broadcast["question"]["id"] == question_data["id"]
            assert broadcast["question"]["question_text"] == "Does WebSocket broadcast work?"
            
            print("✅ TEST PASSED: WebSocket broadcast received correctly!")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: No WebSocket broadcast received!")
            print(f"Error: {e}")
            print(f"Question was created (API returned 201) but WebSocket broadcast failed")
            raise AssertionError("WebSocket broadcast was not sent when question was submitted")


def test_upvote_broadcast_e2e(client, test_event):
    """
    CRITICAL TEST: Verify WebSocket broadcasts when question is upvoted.
    
    This test simulates:
    1. Create and approve a question
    2. WebSocket client connects
    3. Someone upvotes the question
    4. WebSocket should receive upvote broadcast
    """
    # Create and approve question first
    response = client.post(
        f"/api/v1/events/{test_event.id}/questions",
        json={"question_text": "Test upvote"},
        headers={"x-session-id": "creator"}
    )
    question_id = response.json()["id"]
    
    # Approve it
    client.put(
        f"/api/v1/events/{test_event.id}/questions/{question_id}/status",
        json={"status": "approved"},
        headers={"Authorization": f"Host {test_event.host_code}"}
    )
    
    # Connect WebSocket
    with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
        websocket.receive_json()  # Clear connection message
        
        # Upvote the question
        print(f"\n👍 Upvoting question {question_id}...")
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/upvote",
            headers={"x-session-id": "upvoter_456"}
        )
        
        print(f"API Response: {response.status_code} - {response.json()}")
        assert response.status_code == 200
        
        # Wait for broadcast
        try:
            print("\n⏳ Waiting for upvote broadcast...")
            broadcast = websocket.receive_json()
            print(f"✅ Received broadcast: {broadcast}")
            
            assert broadcast["type"] == "question_upvoted"
            assert broadcast["question_id"] == question_id
            assert broadcast["upvote_count"] == 1
            
            print("✅ TEST PASSED: Upvote broadcast received!")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: No upvote broadcast received!")
            print(f"Error: {e}")
            raise AssertionError("WebSocket broadcast was not sent when question was upvoted")


def test_multiple_clients_scenario(client, test_event):
    """
    REALISTIC TEST: Multiple clients connected, all should receive broadcasts.
    
    Simulates:
    - Host dashboard connected
    - 2 Attendees connected
    - When question submitted, all 3 should receive broadcast
    """
    print(f"\n🔌 Connecting 3 WebSocket clients...")
    
    with client.websocket_connect(f"/ws/events/{test_event.slug}") as host_ws, \
         client.websocket_connect(f"/ws/events/{test_event.slug}") as attendee1_ws, \
         client.websocket_connect(f"/ws/events/{test_event.slug}") as attendee2_ws:
        
        # Clear connection messages
        host_ws.receive_json()
        attendee1_ws.receive_json()
        attendee2_ws.receive_json()
        print("✅ All 3 clients connected")
        
        # Submit question
        print(f"\n📝 Submitting question...")
        response = client.post(
            f"/api/v1/events/{test_event.id}/questions",
            json={"question_text": "Everyone should see this"},
            headers={"x-session-id": "broadcaster"}
        )
        assert response.status_code == 201
        question_id = response.json()["id"]
        print(f"✅ Question created: ID={question_id}")
        
        # All 3 clients should receive broadcast
        clients = {"host": host_ws, "attendee1": attendee1_ws, "attendee2": attendee2_ws}
        
        for client_name, ws in clients.items():
            try:
                print(f"\n⏳ Checking {client_name}...")
                broadcast = ws.receive_json()
                print(f"✅ {client_name} received: {broadcast['type']}")
                assert broadcast["type"] == "question_submitted"
                assert broadcast["question"]["id"] == question_id
            except Exception as e:
                print(f"❌ {client_name} did NOT receive broadcast!")
                raise AssertionError(f"{client_name} did not receive WebSocket broadcast")
        
        print("\n✅ TEST PASSED: All clients received broadcast!")


def test_moderation_broadcast(client, test_event):
    """
    TEST: Verify moderation (approval/rejection) broadcasts to all clients.
    """
    # Submit question
    response = client.post(
        f"/api/v1/events/{test_event.id}/questions",
        json={"question_text": "Needs approval"},
        headers={"x-session-id": "submitter"}
    )
    question_id = response.json()["id"]
    
    # Connect WebSocket
    with client.websocket_connect(f"/ws/events/{test_event.slug}") as websocket:
        websocket.receive_json()  # Clear connection
        
        # Host approves
        print(f"\n✅ Host approving question {question_id}...")
        response = client.put(
            f"/api/v1/events/{test_event.id}/questions/{question_id}/status",
            json={"status": "approved"},
            headers={"Authorization": f"Host {test_event.host_code}"}
        )
        assert response.status_code == 200
        
        # Should receive broadcast
        try:
            broadcast = websocket.receive_json()
            print(f"✅ Received: {broadcast}")
            assert broadcast["type"] == "question_submitted"
            assert broadcast["question"]["status"] == "approved"
            print("✅ TEST PASSED: Moderation broadcast works!")
        except Exception as e:
            print(f"❌ No moderation broadcast received!")
            raise AssertionError("Moderation broadcast failed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 RUNNING END-TO-END WEBSOCKET TESTS")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])

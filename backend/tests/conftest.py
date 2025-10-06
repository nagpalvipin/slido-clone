"""
Test configuration and fixtures.

Provides isolated test database and fixtures for all tests.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.core.database import Base, get_db
from src.main import app


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Create test database engine
    test_database_url = f"sqlite:///{db_path}"
    test_engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    def override_get_db():
        """Override database dependency for testing."""
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    # Cleanup
    app.dependency_overrides.clear()
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with isolated database."""
    return TestClient(app)


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "title": "Test Workshop",
        "slug": "test-workshop",
        "description": "A test workshop for automated testing"
    }


def create_test_event(client):
    """Helper function to create a test event."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    event_data = {
        "title": f"Test Workshop {unique_id}",
        "slug": f"test-workshop-{unique_id}",
        "description": f"A test workshop for automated testing - {unique_id}"
    }
    response = client.post("/api/v1/events", json=event_data)
    if response.status_code != 201:
        raise Exception(f"Event creation failed: {response.status_code} - {response.json()}")
    return response.json()
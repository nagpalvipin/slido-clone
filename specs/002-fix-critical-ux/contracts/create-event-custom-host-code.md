# API Contract: POST /api/v1/events (with custom host code)

## Endpoint
```
POST /api/v1/events
```

## Purpose
Create a new event with optional custom host code. If host_code not provided, system generates secure random code.

## Request

### Headers
```
Content-Type: application/json
```

### Body Schema
```json
{
  "title": "string (required, 1-200 chars)",
  "slug": "string (required, 3-50 chars, lowercase, alphanumeric + hyphens)",
  "description": "string (optional, max 1000 chars)",
  "host_code": "string (optional, format: host_[a-z0-9]{12})"
}
```

### Example Request
```json
{
  "title": "Team All-Hands Q&A",
  "slug": "team-allhands-2025",
  "description": "Monthly team meeting with live Q&A",
  "host_code": "host_myteam12345"
}
```

## Responses

### 201 Created
**Condition**: Event created successfully with custom or generated host code

**Body Schema**:
```json
{
  "id": "integer",
  "title": "string",
  "slug": "string",
  "description": "string | null",
  "short_code": "string (attendee access)",
  "host_code": "string (host access - custom or generated)",
  "created_at": "string (ISO 8601)",
  "is_active": "boolean",
  "attendee_count": "integer"
}
```

**Example**:
```json
{
  "id": 42,
  "title": "Team All-Hands Q&A",
  "slug": "team-allhands-2025",
  "description": "Monthly team meeting with live Q&A",
  "short_code": "ABC123",
  "host_code": "host_myteam12345",
  "created_at": "2025-10-08T14:30:00Z",
  "is_active": true,
  "attendee_count": 0
}
```

### 400 Bad Request
**Condition**: Invalid input (title missing, slug format invalid, description too long)

**Body**:
```json
{
  "detail": "Validation error message"
}
```

### 409 Conflict
**Condition**: Host code already in use OR slug already exists

**Body (Host Code Conflict)**:
```json
{
  "detail": "Host code 'host_myteam12345' is already in use. Please choose a different code."
}
```

**Body (Slug Conflict)**:
```json
{
  "detail": "Event slug 'team-allhands-2025' already exists"
}
```

### 422 Unprocessable Entity
**Condition**: Host code format invalid

**Body**:
```json
{
  "detail": "Invalid host code format. Must match pattern: host_[a-z0-9]{12}"
}
```

## Validation Rules

### Title
- Required
- Min length: 1 character
- Max length: 200 characters
- Whitespace trimmed

### Slug
- Required
- Min length: 3 characters
- Max length: 50 characters
- Pattern: `^[a-z0-9-]+$` (lowercase alphanumeric + hyphens)
- Must be unique across all events

### Description
- Optional (can be null/omitted)
- Max length: 1000 characters

### Host Code
- Optional (if omitted, system generates)
- Min length: 17 characters (host_ + 12)
- Max length: 50 characters
- Pattern: `^host_[a-z0-9]{12}$`
- Must be unique across all events
- Case-insensitive (normalized to lowercase)

## Security
- No authentication required for event creation (public feature)
- Host code is sensitive credential - treat as password
- Rate limiting: 10 requests per minute per IP (prevent spam)

## Performance
- Target response time: <100ms
- Database: Single INSERT with unique constraint check
- Concurrent requests: Database handles race conditions via UNIQUE constraint

## Test Scenarios

### Contract Test: Valid Event with Custom Host Code
```python
def test_create_event_with_custom_host_code():
    response = client.post("/api/v1/events", json={
        "title": "Test Event",
        "slug": "test-event-unique",
        "host_code": "host_test1234567"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["host_code"] == "host_test1234567"
    assert "short_code" in data
    assert data["is_active"] == True
```

### Contract Test: Event Without Custom Host Code (Auto-generate)
```python
def test_create_event_auto_generate_host_code():
    response = client.post("/api/v1/events", json={
        "title": "Test Event",
        "slug": "test-event-auto"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["host_code"].startswith("host_")
    assert len(data["host_code"]) == 17
```

### Contract Test: Duplicate Host Code
```python
def test_create_event_duplicate_host_code():
    # Create first event
    client.post("/api/v1/events", json={
        "title": "Event 1",
        "slug": "event-1",
        "host_code": "host_duplicate01"
    })
    
    # Attempt duplicate
    response = client.post("/api/v1/events", json={
        "title": "Event 2",
        "slug": "event-2",
        "host_code": "host_duplicate01"
    })
    assert response.status_code == 409
    assert "already in use" in response.json()["detail"]
```

### Contract Test: Invalid Host Code Format
```python
def test_create_event_invalid_host_code_format():
    response = client.post("/api/v1/events", json={
        "title": "Test Event",
        "slug": "test-event",
        "host_code": "invalid-code"  # Wrong format
    })
    assert response.status_code == 422
    assert "Invalid host code format" in response.json()["detail"]
```

### Contract Test: Host Code Too Short
```python
def test_create_event_host_code_too_short():
    response = client.post("/api/v1/events", json={
        "title": "Test Event",
        "slug": "test-event",
        "host_code": "host_short"  # Only 5 chars after host_
    })
    assert response.status_code == 422
```

## Implementation Notes
- Backend must normalize host_code to lowercase before database check
- Auto-generated codes use cryptographically secure random (secrets module)
- Short code generation remains unchanged (existing logic)
- Database transaction ensures atomic create with unique check

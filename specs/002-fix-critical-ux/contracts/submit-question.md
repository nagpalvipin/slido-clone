# API Contract: POST /api/v1/events/{event_id}/questions

## Endpoint
```
POST /api/v1/events/{event_id}/questions
```

## Purpose
Allow attendees to submit questions to an event. Implements FR-001 (1-1000 character validation) and FR-004 (visual confirmation via response payload).

## Request

### Headers
```
Content-Type: application/json
Authorization: Attendee {attendee_id}
```

### Path Parameters
- `event_id`: integer - ID of the event to submit question to

### Body Schema
```json
{
  "text": "string (1-1000 characters, required)",
  "is_anonymous": "boolean (optional, default=false)"
}
```

### Example Request
```http
POST /api/v1/events/42/questions
Content-Type: application/json
Authorization: Attendee attendee_abc123def456

{
  "text": "What is the expected timeline for the new feature rollout?",
  "is_anonymous": false
}
```

## Responses

### 201 Created
**Condition**: Question successfully created

**Body Schema**:
```json
{
  "id": "integer",
  "event_id": "integer",
  "text": "string",
  "is_anonymous": "boolean",
  "author_name": "string | null (null if anonymous)",
  "upvote_count": "integer (always 0 for new question)",
  "created_at": "string (ISO 8601)",
  "is_answered": "boolean (always false for new question)",
  "user_has_upvoted": "boolean (always false for new question)"
}
```

**Example**:
```json
{
  "id": 1001,
  "event_id": 42,
  "text": "What is the expected timeline for the new feature rollout?",
  "is_anonymous": false,
  "author_name": "Alice Johnson",
  "upvote_count": 0,
  "created_at": "2025-10-08T15:45:22Z",
  "is_answered": false,
  "user_has_upvoted": false
}
```

**Note**: Frontend uses this response to display the question immediately with highlight animation (FR-004 clarification).

### 400 Bad Request
**Condition**: Validation failure

**Scenarios**:
1. **Empty or whitespace-only text**
```json
{
  "detail": "Question text must be between 1 and 1000 characters"
}
```

2. **Text too long (>1000 chars)**
```json
{
  "detail": "Question text must be between 1 and 1000 characters"
}
```

3. **Missing required field**
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 404 Not Found
**Condition**: Event does not exist

**Body**:
```json
{
  "detail": "Event not found"
}
```

### 422 Unprocessable Entity
**Condition**: Invalid JSON or type mismatch

**Example**:
```json
{
  "detail": [
    {
      "loc": ["body", "is_anonymous"],
      "msg": "value is not a valid boolean",
      "type": "type_error.bool"
    }
  ]
}
```

### 429 Too Many Requests
**Condition**: Rate limit exceeded (10 questions/minute per attendee)

**Body**:
```json
{
  "detail": "Rate limit exceeded. Maximum 10 questions per minute."
}
```

**Headers**:
```
Retry-After: 42 (seconds until reset)
```

### 500 Internal Server Error
**Condition**: Database or system failure

**Body**:
```json
{
  "detail": "Internal server error"
}
```

## Validation Rules

### Text Field
- **Required**: Yes
- **Min Length**: 1 (after trimming whitespace)
- **Max Length**: 1000
- **Allowed Characters**: Any Unicode characters
- **Trimming**: Leading/trailing whitespace removed before validation
- **Examples**:
  - ✅ "How does this work?" (valid)
  - ✅ "Can you explain 🚀 the new feature?" (emoji allowed)
  - ✅ String with 1000 characters (valid)
  - ❌ "" (empty)
  - ❌ "   " (whitespace only)
  - ❌ String with 1001 characters (too long)

### is_anonymous Field
- **Required**: No
- **Default**: false
- **Type**: Boolean
- **Effect**: When true, `author_name` is null in response and stored as null in DB

## Authorization
- Requires valid attendee identifier in `Authorization` header
- Format: `Attendee {attendee_id}` (e.g., generated UUID or session ID)
- No host/admin permissions needed (public submission)

## Performance
- Target response time: <500ms (per NFR-001)
- Database insert + WebSocket broadcast
- Async WebSocket notification (non-blocking)

## Real-Time Behavior
Upon successful creation (201 response):
1. Question persisted to database
2. WebSocket message broadcast to event room:
```json
{
  "type": "question_created",
  "event_id": 42,
  "question": {
    "id": 1001,
    "event_id": 42,
    "text": "What is the expected timeline?",
    "is_anonymous": false,
    "author_name": "Alice Johnson",
    "upvote_count": 0,
    "created_at": "2025-10-08T15:45:22Z",
    "is_answered": false
  }
}
```
3. All connected clients (host dashboard + attendee views) receive update
4. Frontend displays with highlight animation (FR-004)

## Test Scenarios

### Contract Test: Valid Question Submission
```python
def test_submit_question_success():
    event = create_event("Test Event", "test-event", "host_test123")
    attendee_id = "attendee_alice123"
    
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": "How does this feature work?", "is_anonymous": False},
        headers={"Authorization": f"Attendee {attendee_id}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["text"] == "How does this feature work?"
    assert data["is_anonymous"] is False
    assert data["upvote_count"] == 0
    assert data["is_answered"] is False
    assert "created_at" in data
```

### Contract Test: Anonymous Submission
```python
def test_submit_anonymous_question():
    event = create_event("Test Event", "test", "host_test123")
    
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": "Anonymous question here", "is_anonymous": True},
        headers={"Authorization": "Attendee attendee_anon456"}
    )
    
    data = response.json()
    assert data["is_anonymous"] is True
    assert data["author_name"] is None
```

### Contract Test: Text Length Validation (Minimum)
```python
def test_submit_question_empty_text():
    event = create_event("Test Event", "test", "host_test123")
    
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": ""},
        headers={"Authorization": "Attendee attendee_test123"}
    )
    
    assert response.status_code == 400
    assert "between 1 and 1000 characters" in response.json()["detail"]

def test_submit_question_whitespace_only():
    event = create_event("Test Event", "test", "host_test123")
    
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": "   \n\t  "},
        headers={"Authorization": "Attendee attendee_test123"}
    )
    
    assert response.status_code == 400
```

### Contract Test: Text Length Validation (Maximum)
```python
def test_submit_question_max_length():
    event = create_event("Test Event", "test", "host_test123")
    text_1000 = "a" * 1000
    
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": text_1000},
        headers={"Authorization": "Attendee attendee_test123"}
    )
    
    assert response.status_code == 201

def test_submit_question_exceeds_max_length():
    event = create_event("Test Event", "test", "host_test123")
    text_1001 = "a" * 1001
    
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": text_1001},
        headers={"Authorization": "Attendee attendee_test123"}
    )
    
    assert response.status_code == 400
    assert "between 1 and 1000 characters" in response.json()["detail"]
```

### Contract Test: Event Not Found
```python
def test_submit_question_event_not_found():
    response = client.post(
        "/api/v1/events/99999/questions",
        json={"text": "Question for non-existent event"},
        headers={"Authorization": "Attendee attendee_test123"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"
```

### Contract Test: Missing Required Field
```python
def test_submit_question_missing_text():
    event = create_event("Test Event", "test", "host_test123")
    
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"is_anonymous": False},  # Missing 'text'
        headers={"Authorization": "Attendee attendee_test123"}
    )
    
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert any("text" in str(err) and "required" in str(err) for err in detail)
```

### Contract Test: Unicode Support
```python
def test_submit_question_unicode_text():
    event = create_event("Test Event", "test", "host_test123")
    
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": "How does 🚀 this 日本語 feature работать?"},
        headers={"Authorization": "Attendee attendee_test123"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "How does 🚀 this 日本語 feature работать?"
```

### Contract Test: Rate Limiting
```python
def test_submit_question_rate_limit():
    event = create_event("Test Event", "test", "host_test123")
    attendee_id = "attendee_spammer123"
    
    # Submit 10 questions (within limit)
    for i in range(10):
        response = client.post(
            f"/api/v1/events/{event.id}/questions",
            json={"text": f"Question {i}"},
            headers={"Authorization": f"Attendee {attendee_id}"}
        )
        assert response.status_code == 201
    
    # 11th request should be rate limited
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": "Question 11"},
        headers={"Authorization": f"Attendee {attendee_id}"}
    )
    
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
    assert "Retry-After" in response.headers
```

## Performance Test Scenarios

### Submission Latency (<500ms Target)
```python
def test_submit_question_performance():
    event = create_event("Test Event", "test", "host_test123")
    
    start = time.time()
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": "Performance test question"},
        headers={"Authorization": "Attendee attendee_perf123"}
    )
    duration = time.time() - start
    
    assert response.status_code == 201
    assert duration < 0.5  # <500ms target per NFR-001
```

### Concurrent Submissions
```python
def test_submit_questions_concurrent():
    event = create_event("Test Event", "test", "host_test123")
    
    def submit_question(i):
        return client.post(
            f"/api/v1/events/{event.id}/questions",
            json={"text": f"Concurrent question {i}"},
            headers={"Authorization": f"Attendee attendee_{i}"}
        )
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(submit_question, range(10)))
    
    # All submissions should succeed
    assert all(r.status_code == 201 for r in responses)
    # All questions should have unique IDs
    ids = [r.json()["id"] for r in responses]
    assert len(ids) == len(set(ids))
```

## Frontend Integration

### QuestionSubmit Component Usage
```typescript
async function handleQuestionSubmit(text: string, isAnonymous: boolean) {
  try {
    const response = await api.post(`/events/${eventId}/questions`, {
      text: text.trim(),
      is_anonymous: isAnonymous
    }, {
      headers: { Authorization: `Attendee ${attendeeId}` }
    });

    const question = response.data;
    
    // Display with highlight animation (FR-004)
    addQuestionToList(question, { highlight: true });
    
    // Clear form
    resetForm();
    
    showToast('Question submitted successfully!', 'success');
  } catch (error) {
    if (error.response?.status === 429) {
      showToast('You are submitting too quickly. Please wait.', 'warning');
    } else {
      showToast('Failed to submit question. Please try again.', 'error');
    }
  }
}
```

## Implementation Checklist
- [ ] Create POST /events/{event_id}/questions endpoint
- [ ] Add text length validation (1-1000 chars)
- [ ] Implement attendee authentication
- [ ] Add rate limiting (10 req/min per attendee)
- [ ] Implement anonymous submission logic
- [ ] Add WebSocket broadcast on creation
- [ ] Write contract tests (all scenarios above)
- [ ] Add performance tests (<500ms latency)
- [ ] Update frontend QuestionSubmit component
- [ ] Add highlight animation for new questions

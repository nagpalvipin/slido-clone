# API Contract: GET /api/v1/events/{event_id}/questions

## Endpoint
```
GET /api/v1/events/{event_id}/questions
```

## Purpose
Retrieve all questions for an event (host view) with proper vote counting and ordering. **FIXED**: Now uses SQL subquery instead of Python property for sorting.

## Request

### Path Parameters
- `event_id`: integer (required) - ID of the event

### Headers
```
Authorization: Host {host_code}
```

### Query Parameters
None

## Responses

### 200 OK
**Condition**: Successfully retrieved questions with vote counts

**Body Schema**:
```json
[
  {
    "id": "integer",
    "question_text": "string",
    "status": "string (submitted|approved|answered|rejected)",
    "created_at": "string (ISO 8601)",
    "upvote_count": "integer"
  }
]
```

**Ordering**:
1. By `upvote_count` DESC (highest votes first)
2. Questions with 0 votes last (NULLSLAST)
3. Within same vote count, by `created_at` ASC (oldest first)

**Example**:
```json
[
  {
    "id": 1,
    "question_text": "What is our Q4 strategy?",
    "status": "submitted",
    "created_at": "2025-10-08T14:00:00Z",
    "upvote_count": 15
  },
  {
    "id": 2,
    "question_text": "When will the new feature launch?",
    "status": "approved",
    "created_at": "2025-10-08T14:05:00Z",
    "upvote_count": 8
  },
  {
    "id": 3,
    "question_text": "How do we handle edge cases?",
    "status": "submitted",
    "created_at": "2025-10-08T14:10:00Z",
    "upvote_count": 0
  }
]
```

### 401 Unauthorized
**Condition**: Missing or invalid host code

**Body**:
```json
{
  "detail": "Authorization header required"
}
```

OR

```json
{
  "detail": "Invalid host code"
}
```

### 404 Not Found
**Condition**: Event with given ID does not exist

**Body**:
```json
{
  "detail": "Event not found"
}
```

## Authorization
- Requires valid host code in `Authorization` header
- Format: `Authorization: Host host_xxxxxxxxxxxxx`
- Host code must match the event's host_code
- Validates host access before returning questions

## Performance
- Target response time: <200ms
- Uses optimized SQL subquery for vote counting
- Indexed queries on event_id and foreign keys

## SQL Implementation (Reference)

**BROKEN (Previous)**:
```python
# This fails - upvote_count is a @property, not a column
questions = db.query(Question).order_by(Question.upvote_count.desc())
# AttributeError: 'property' object has no attribute 'desc'
```

**FIXED (Current)**:
```python
# Subquery for vote counts
vote_count_subquery = db.query(
    QuestionVote.question_id,
    func.count(QuestionVote.id).label('vote_count')
).group_by(QuestionVote.question_id).subquery()

# Main query with join
questions = db.query(Question).filter(
    Question.event_id == event_id
).outerjoin(
    vote_count_subquery,
    Question.id == vote_count_subquery.c.question_id
).order_by(
    vote_count_subquery.c.vote_count.desc().nullslast(),
    Question.created_at.asc()
).all()
```

## Test Scenarios

### Contract Test: Get Questions with Votes
```python
def test_get_questions_with_vote_counts():
    # Setup: Create event and questions with votes
    event = create_test_event()
    q1 = create_question(event.id, "Question 1")
    q2 = create_question(event.id, "Question 2")
    add_votes(q1.id, count=5)
    add_votes(q2.id, count=2)
    
    # Request
    response = client.get(
        f"/api/v1/events/{event.id}/questions",
        headers={"Authorization": f"Host {event.host_code}"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == q1.id  # Highest votes first
    assert data[0]["upvote_count"] == 5
    assert data[1]["id"] == q2.id
    assert data[1]["upvote_count"] == 2
```

### Contract Test: Questions Without Votes
```python
def test_get_questions_zero_votes_ordered_correctly():
    event = create_test_event()
    q1 = create_question(event.id, "First question", created_at="2025-10-08T14:00:00Z")
    q2 = create_question(event.id, "Second question", created_at="2025-10-08T14:05:00Z")
    # No votes added
    
    response = client.get(
        f"/api/v1/events/{event.id}/questions",
        headers={"Authorization": f"Host {event.host_code}"}
    )
    
    data = response.json()
    assert data[0]["id"] == q1.id  # Older first when votes are equal
    assert data[0]["upvote_count"] == 0
    assert data[1]["upvote_count"] == 0
```

### Contract Test: Unauthorized Access
```python
def test_get_questions_no_auth_header():
    event = create_test_event()
    response = client.get(f"/api/v1/events/{event.id}/questions")
    assert response.status_code == 401
    assert "Authorization header required" in response.json()["detail"]
```

### Contract Test: Invalid Host Code
```python
def test_get_questions_wrong_host_code():
    event = create_test_event()
    response = client.get(
        f"/api/v1/events/{event.id}/questions",
        headers={"Authorization": "Host host_wrongcode123"}
    )
    assert response.status_code == 401
    assert "Invalid host code" in response.json()["detail"]
```

### Contract Test: Event Not Found
```python
def test_get_questions_event_not_found():
    response = client.get(
        "/api/v1/events/99999/questions",
        headers={"Authorization": "Host host_anycode12345"}
    )
    assert response.status_code == 404
```

### Contract Test: Real-Time Update Integration
```python
async def test_questions_appear_in_realtime():
    """Integration: Attendee submits → Host sees within 2s"""
    event = create_test_event()
    
    # Host connects to WebSocket
    async with websocket_client(f"/ws/{event.slug}") as ws_host:
        # Attendee submits question
        response = client.post(
            f"/api/v1/events/{event.id}/questions",
            json={"question_text": "Real-time test question"}
        )
        assert response.status_code == 201
        
        # Host receives WebSocket message
        message = await asyncio.wait_for(ws_host.recv(), timeout=2.0)
        assert message["type"] == "question_created"
        
        # Host fetches updated list
        questions_response = client.get(
            f"/api/v1/events/{event.id}/questions",
            headers={"Authorization": f"Host {event.host_code}"}
        )
        data = questions_response.json()
        assert any(q["question_text"] == "Real-time test question" for q in data)
```

## Edge Cases

### Empty Event (No Questions)
```python
def test_get_questions_empty_event():
    event = create_test_event()
    response = client.get(
        f"/api/v1/events/{event.id}/questions",
        headers={"Authorization": f"Host {event.host_code}"}
    )
    assert response.status_code == 200
    assert response.json() == []
```

### Large Number of Questions (Performance)
```python
def test_get_questions_large_dataset():
    event = create_test_event()
    # Create 1000 questions with varying vote counts
    for i in range(1000):
        q = create_question(event.id, f"Question {i}")
        add_votes(q.id, count=random.randint(0, 100))
    
    start = time.time()
    response = client.get(
        f"/api/v1/events/{event.id}/questions",
        headers={"Authorization": f"Host {event.host_code}"}
    )
    duration = time.time() - start
    
    assert response.status_code == 200
    assert len(response.json()) == 1000
    assert duration < 0.2  # <200ms target
```

## Implementation Checklist
- [x] Fix SQL query to use subquery instead of property
- [ ] Add index on (question_votes.question_id) for performance
- [ ] Validate Authorization header format
- [ ] Return proper error codes (401, 404)
- [ ] Add integration tests for real-time flow
- [ ] Performance test with 1000+ questions

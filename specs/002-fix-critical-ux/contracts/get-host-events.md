# API Contract: GET /api/v1/events/host

## Endpoint
```
GET /api/v1/events/host
```

## Purpose
Retrieve paginated list of events created by the authenticated host. Used for event switcher dropdown and multi-event management.

## Request

### Headers
```
Authorization: Host {host_code}
```

### Query Parameters
- `page`: integer (optional, default=1, min=1) - Page number
- `per_page`: integer (optional, default=20, min=1, max=100) - Items per page

### Example Request
```
GET /api/v1/events/host?page=1&per_page=20
Authorization: Host host_myteam12345
```

## Responses

### 200 OK
**Condition**: Successfully retrieved host's events

**Body Schema**:
```json
{
  "events": [
    {
      "id": "integer",
      "title": "string",
      "slug": "string",
      "short_code": "string",
      "created_at": "string (ISO 8601)",
      "is_active": "boolean",
      "question_count": "integer",
      "poll_count": "integer"
    }
  ],
  "total": "integer (total events across all pages)",
  "page": "integer (current page)",
  "per_page": "integer (items per page)",
  "total_pages": "integer (calculated: ceil(total / per_page))"
}
```

**Ordering**: By `created_at` DESC (newest first)

**Example**:
```json
{
  "events": [
    {
      "id": 42,
      "title": "Team All-Hands Q&A",
      "slug": "team-allhands-2025",
      "short_code": "ABC123",
      "created_at": "2025-10-08T14:30:00Z",
      "is_active": true,
      "question_count": 15,
      "poll_count": 3
    },
    {
      "id": 41,
      "title": "Product Launch Event",
      "slug": "product-launch-oct",
      "short_code": "XYZ789",
      "created_at": "2025-10-01T10:00:00Z",
      "is_active": false,
      "question_count": 42,
      "poll_count": 5
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
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

### 400 Bad Request
**Condition**: Invalid pagination parameters

**Body**:
```json
{
  "detail": "Page must be >= 1"
}
```

OR

```json
{
  "detail": "Per page must be between 1 and 100"
}
```

## Authorization
- Requires valid host code in `Authorization` header
- Returns only events where `event.host_code` matches provided code
- No cross-host access (host can only see their own events)

## Performance
- Target response time: <100ms for 20 events
- Indexed query on (host_code, created_at)
- Counts computed via subqueries (not N+1 queries)

## Pagination Behavior

### First Page
```
GET /api/v1/events/host?page=1&per_page=20
→ Returns events 1-20 (or fewer if less than 20 total)
```

### Middle Page
```
GET /api/v1/events/host?page=2&per_page=20
→ Returns events 21-40
```

### Last Page
```
GET /api/v1/events/host?page=3&per_page=20
→ Returns remaining events (e.g., 41-45 if total=45)
```

### Beyond Last Page
```
GET /api/v1/events/host?page=10&per_page=20 (when total_pages=3)
→ Returns {"events": [], "total": 45, "page": 10, "per_page": 20, "total_pages": 3}
```

## SQL Implementation (Reference)

```python
# Count total events for this host
total = db.query(Event).filter(Event.host_code == host_code).count()

# Fetch paginated events with counts
events = db.query(
    Event,
    func.count(Question.id).label('question_count'),
    func.count(Poll.id).label('poll_count')
).outerjoin(Question).outerjoin(Poll).filter(
    Event.host_code == host_code
).group_by(Event.id).order_by(
    Event.created_at.desc()
).offset((page - 1) * per_page).limit(per_page).all()

# Calculate total pages
total_pages = (total + per_page - 1) // per_page  # Ceiling division

return {
    "events": [serialize(e) for e in events],
    "total": total,
    "page": page,
    "per_page": per_page,
    "total_pages": total_pages
}
```

## Test Scenarios

### Contract Test: Get First Page
```python
def test_get_host_events_first_page():
    host_code = "host_test12345678"
    # Create 25 events with this host code
    for i in range(25):
        create_event(f"Event {i}", f"event-{i}", host_code)
    
    response = client.get(
        "/api/v1/events/host?page=1&per_page=20",
        headers={"Authorization": f"Host {host_code}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 20
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["total_pages"] == 2
```

### Contract Test: Get Last Page (Partial)
```python
def test_get_host_events_last_page():
    host_code = "host_test12345678"
    # Create 45 events
    for i in range(45):
        create_event(f"Event {i}", f"event-{i}", host_code)
    
    response = client.get(
        "/api/v1/events/host?page=3&per_page=20",
        headers={"Authorization": f"Host {host_code}"}
    )
    
    data = response.json()
    assert len(data["events"]) == 5  # 45 - 40 = 5 remaining
    assert data["total"] == 45
    assert data["total_pages"] == 3
```

### Contract Test: No Events
```python
def test_get_host_events_empty():
    host_code = "host_newhost1234"
    response = client.get(
        "/api/v1/events/host",
        headers={"Authorization": f"Host {host_code}"}
    )
    
    data = response.json()
    assert data["events"] == []
    assert data["total"] == 0
    assert data["total_pages"] == 0
```

### Contract Test: Ordering (Newest First)
```python
def test_get_host_events_ordered_by_created_at():
    host_code = "host_test12345678"
    old_event = create_event("Old Event", "old", host_code, created_at="2025-01-01T00:00:00Z")
    new_event = create_event("New Event", "new", host_code, created_at="2025-10-08T00:00:00Z")
    
    response = client.get(
        "/api/v1/events/host",
        headers={"Authorization": f"Host {host_code}"}
    )
    
    data = response.json()
    assert data["events"][0]["id"] == new_event.id  # Newest first
    assert data["events"][1]["id"] == old_event.id
```

### Contract Test: Question/Poll Counts
```python
def test_get_host_events_includes_counts():
    host_code = "host_test12345678"
    event = create_event("Event with Content", "event-1", host_code)
    create_questions(event.id, count=10)
    create_polls(event.id, count=3)
    
    response = client.get(
        "/api/v1/events/host",
        headers={"Authorization": f"Host {host_code}"}
    )
    
    data = response.json()
    assert data["events"][0]["question_count"] == 10
    assert data["events"][0]["poll_count"] == 3
```

### Contract Test: Host Isolation
```python
def test_get_host_events_only_own_events():
    host1_code = "host_host1234567"
    host2_code = "host_other123456"
    
    create_event("Host 1 Event 1", "h1-e1", host1_code)
    create_event("Host 1 Event 2", "h1-e2", host1_code)
    create_event("Host 2 Event 1", "h2-e1", host2_code)
    
    response = client.get(
        "/api/v1/events/host",
        headers={"Authorization": f"Host {host1_code}"}
    )
    
    data = response.json()
    assert len(data["events"]) == 2  # Only host 1's events
    assert all(e["slug"].startswith("h1-") for e in data["events"])
```

### Contract Test: Invalid Pagination
```python
def test_get_host_events_invalid_page():
    response = client.get(
        "/api/v1/events/host?page=0",
        headers={"Authorization": "Host host_test12345678"}
    )
    assert response.status_code == 400
    assert "Page must be >= 1" in response.json()["detail"]

def test_get_host_events_per_page_too_large():
    response = client.get(
        "/api/v1/events/host?per_page=200",
        headers={"Authorization": "Host host_test12345678"}
    )
    assert response.status_code == 400
    assert "between 1 and 100" in response.json()["detail"]
```

### Contract Test: Unauthorized Access
```python
def test_get_host_events_no_auth():
    response = client.get("/api/v1/events/host")
    assert response.status_code == 401
    assert "Authorization header required" in response.json()["detail"]
```

## Performance Test Scenarios

### Large Dataset (100+ Events)
```python
def test_get_host_events_performance_large_dataset():
    host_code = "host_perf12345678"
    # Create 100 events
    for i in range(100):
        event = create_event(f"Event {i}", f"perf-event-{i}", host_code)
        create_questions(event.id, count=random.randint(0, 50))
    
    start = time.time()
    response = client.get(
        "/api/v1/events/host?page=1&per_page=20",
        headers={"Authorization": f"Host {host_code}"}
    )
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 0.1  # <100ms target
```

## Frontend Integration

### EventSwitcher Component Usage
```typescript
// Fetch first page
const response = await api.get('/events/host?page=1&per_page=20', {
  headers: { Authorization: `Host ${hostCode}` }
});

const { events, total, page, per_page, total_pages } = response.data;

// Display in dropdown with pagination controls
<EventDropdown
  events={events}
  onSelect={handleEventSelect}
  pagination={{ page, totalPages: total_pages }}
  onPageChange={handlePageChange}
/>
```

## Implementation Checklist
- [ ] Create new GET /events/host endpoint
- [ ] Add host code authentication middleware
- [ ] Implement pagination logic
- [ ] Add subqueries for question/poll counts
- [ ] Create composite index on (host_code, created_at)
- [ ] Write contract tests (all scenarios above)
- [ ] Add performance tests for 100+ events
- [ ] Update frontend API client
- [ ] Build EventSwitcher component

# Polls API Contract

**Base URL**: `/api/v1/events/{event_id}/polls`  
**Host Authentication**: Required for creation and management  
**Attendee Access**: Read-only for active polls

## POST /api/v1/events/{event_id}/polls
Create a new poll (host only).

### Headers
```
Authorization: Host host_9f8e7d6c5b4a
```

### Request
```json
{
  "question_text": "Which topic should we cover next?",
  "poll_type": "single",
  "options": [
    {"option_text": "Async/Await Patterns", "position": 0},
    {"option_text": "Error Handling", "position": 1},
    {"option_text": "Performance Optimization", "position": 2},
    {"option_text": "Testing Strategies", "position": 3}
  ]
}
```

### Response (201 Created)
```json
{
  "id": 2,
  "question_text": "Which topic should we cover next?",
  "poll_type": "single",
  "status": "draft",
  "created_at": "2025-10-06T14:45:00Z",
  "options": [
    {
      "id": 5,
      "option_text": "Async/Await Patterns",
      "position": 0,
      "vote_count": 0
    },
    {
      "id": 6,
      "option_text": "Error Handling", 
      "position": 1,
      "vote_count": 0
    },
    {
      "id": 7,
      "option_text": "Performance Optimization",
      "position": 2,
      "vote_count": 0
    },
    {
      "id": 8,
      "option_text": "Testing Strategies",
      "position": 3,
      "vote_count": 0
    }
  ]
}
```

### Validation Rules
- `question_text`: Required, 1-1000 characters
- `poll_type`: Required, enum ['single', 'multi']
- `options`: Required, 2-10 options, each with option_text (1-500 chars) and position

---

## PUT /api/v1/events/{event_id}/polls/{poll_id}/status
Open or close a poll (host only).

### Headers
```
Authorization: Host host_9f8e7d6c5b4a
```

### Request
```json
{
  "status": "open"
}
```

### Response (200 OK)
```json
{
  "id": 2,
  "status": "open",
  "opened_at": "2025-10-06T14:50:00Z"
}
```

### Validation Rules
- `status`: Required, enum ['open', 'closed']
- Cannot reopen closed polls
- Only draft or open polls can be modified

---

## GET /api/v1/events/{event_id}/polls
List all polls for an event.

### Query Parameters
- `status`: Optional filter, enum ['draft', 'open', 'closed']
- `include_results`: Boolean, default true

### Response (200 OK)
```json
{
  "polls": [
    {
      "id": 1,
      "question_text": "What's your JavaScript experience?",
      "poll_type": "single",
      "status": "closed",
      "created_at": "2025-10-06T14:30:00Z",
      "opened_at": "2025-10-06T14:31:00Z",
      "closed_at": "2025-10-06T14:40:00Z",
      "total_votes": 18,
      "options": [
        {
          "id": 1,
          "option_text": "Beginner",
          "position": 0,
          "vote_count": 5,
          "percentage": 27.8
        },
        {
          "id": 2,
          "option_text": "Intermediate",
          "position": 1,
          "vote_count": 10,
          "percentage": 55.6
        },
        {
          "id": 3,
          "option_text": "Advanced",
          "position": 2,
          "vote_count": 3,
          "percentage": 16.7
        }
      ]
    }
  ]
}
```

---

## POST /api/v1/events/{event_id}/polls/{poll_id}/vote
Submit vote(s) for a poll (attendee action).

### Headers
```
X-Attendee-Session: session_abc123def456
```

### Request (Single Choice)
```json
{
  "option_ids": [2]
}
```

### Request (Multi Choice)
```json
{
  "option_ids": [1, 3, 4]
}
```

### Response (201 Created)
```json
{
  "poll_id": 1,
  "votes_recorded": 1,
  "created_at": "2025-10-06T14:52:00Z"
}
```

### Error Response (400 Bad Request)
```json
{
  "error": "Poll is not open for voting",
  "code": "POLL_NOT_OPEN"
}
```

### Error Response (409 Conflict) 
```json
{
  "error": "You have already voted on this poll",
  "code": "ALREADY_VOTED"
}
```

### Validation Rules
- Poll must have status 'open'
- Attendee must be registered for the event
- Single-choice polls: exactly 1 option_id required
- Multi-choice polls: 1-N option_ids allowed
- Cannot vote twice on same poll
- All option_ids must belong to the specified poll

---

## DELETE /api/v1/events/{event_id}/polls/{poll_id}
Delete a poll (host only, draft status only).

### Headers
```
Authorization: Host host_9f8e7d6c5b4a
```

### Response (204 No Content)

### Error Response (400 Bad Request)
```json
{
  "error": "Cannot delete poll that has been opened",
  "code": "POLL_NOT_DRAFT"
}
```
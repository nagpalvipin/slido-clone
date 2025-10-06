# Questions API Contract

**Base URL**: `/api/v1/events/{event_id}/questions`  
**Host Authentication**: Required for moderation actions  
**Attendee Access**: Submit questions and upvote

## POST /api/v1/events/{event_id}/questions
Submit a new question (attendee action).

### Headers
```
X-Attendee-Session: session_abc123def456
X-Attendee-Name: Sarah Chen (optional)
```

### Request
```json
{
  "question_text": "How do you handle race conditions in React with useEffect?"
}
```

### Response (201 Created)
```json
{
  "id": 15,
  "question_text": "How do you handle race conditions in React with useEffect?",
  "status": "pending",
  "upvote_count": 0,
  "created_at": "2025-10-06T14:55:00Z",
  "attendee": {
    "display_name": "Sarah Chen",
    "is_anonymous": false
  }
}
```

### Validation Rules
- `question_text`: Required, 10-1000 characters
- Attendee must be registered for event
- Maximum 5 questions per attendee per event
- Questions auto-assigned 'pending' status

---

## GET /api/v1/events/{event_id}/questions
List questions for an event (filtered by status and role).

### Query Parameters
- `status`: Optional, enum ['pending', 'approved', 'rejected']
- `order_by`: Optional, enum ['votes', 'created'], default 'votes'

### Response for Attendees (approved questions only)
```json
{
  "questions": [
    {
      "id": 12,
      "question_text": "What are the best practices for async error handling?",
      "status": "approved", 
      "upvote_count": 8,
      "created_at": "2025-10-06T14:45:00Z",
      "attendee": {
        "display_name": "Anonymous",
        "is_anonymous": true
      },
      "user_has_upvoted": false
    },
    {
      "id": 10,
      "question_text": "How do closures work in event handlers?",
      "status": "approved",
      "upvote_count": 5,
      "created_at": "2025-10-06T14:40:00Z", 
      "attendee": {
        "display_name": "Mike Rodriguez",
        "is_anonymous": false
      },
      "user_has_upvoted": true
    }
  ]
}
```

### Response for Hosts (all questions)
```json
{
  "questions": [
    {
      "id": 15,
      "question_text": "How do you handle race conditions in React with useEffect?",
      "status": "pending",
      "upvote_count": 2,
      "created_at": "2025-10-06T14:55:00Z",
      "attendee": {
        "display_name": "Sarah Chen", 
        "is_anonymous": false
      }
    }
  ]
}
```

---

## POST /api/v1/events/{event_id}/questions/{question_id}/upvote
Upvote a question (attendee action).

### Headers
```
X-Attendee-Session: session_abc123def456
```

### Response (201 Created)
```json
{
  "question_id": 12,
  "upvoted": true,
  "new_upvote_count": 9,
  "created_at": "2025-10-06T14:56:00Z"
}
```

### Error Response (409 Conflict)
```json
{
  "error": "You have already upvoted this question",
  "code": "ALREADY_UPVOTED"
}
```

### Validation Rules
- Question must have status 'approved'
- Attendee must be registered for event
- Cannot upvote same question twice
- Cannot upvote own questions

---

## PUT /api/v1/events/{event_id}/questions/{question_id}/status
Moderate a question (host only).

### Headers
```
Authorization: Host host_9f8e7d6c5b4a
```

### Request (Approve)
```json
{
  "status": "approved"
}
```

### Request (Reject)
```json
{
  "status": "rejected",
  "reason": "Off-topic for this session"
}
```

### Response (200 OK)
```json
{
  "id": 15,
  "status": "approved",
  "moderated_at": "2025-10-06T14:57:00Z"
}
```

### Validation Rules
- `status`: Required, enum ['approved', 'rejected']
- `reason`: Optional for approval, recommended for rejection
- Only pending questions can be moderated
- Action is irreversible

---

## PUT /api/v1/events/{event_id}/questions/{question_id}/answered
Mark question as answered (host only).

### Headers
```
Authorization: Host host_9f8e7d6c5b4a
```

### Request
```json
{
  "is_answered": true
}
```

### Response (200 OK)
```json
{
  "id": 12,
  "is_answered": true,
  "answered_at": "2025-10-06T15:05:00Z"
}
```

### Validation Rules
- Question must have status 'approved'
- Action is reversible (can mark as unanswered)
- Answered questions remain in queue but visually distinguished

---

## DELETE /api/v1/events/{event_id}/questions/{question_id}
Delete a question (host only or question author).

### Headers
```
Authorization: Host host_9f8e7d6c5b4a
# OR
X-Attendee-Session: session_abc123def456
```

### Response (204 No Content)

### Validation Rules
- Hosts can delete any question
- Attendees can only delete their own questions
- Deletion removes all associated upvotes
- Action is irreversible

---

## WebSocket Events

### Question Status Updates
Broadcast to all event participants when question status changes.

```json
{
  "event_type": "question_status_changed",
  "question_id": 15,
  "new_status": "approved",
  "timestamp": "2025-10-06T14:57:00Z"
}
```

### Question Upvote Updates
Broadcast to all event participants when upvote count changes.

```json
{
  "event_type": "question_upvoted", 
  "question_id": 12,
  "new_upvote_count": 9,
  "timestamp": "2025-10-06T14:56:00Z"
}
```

### New Question Submitted
Broadcast to hosts only when new question is submitted.

```json
{
  "event_type": "question_submitted",
  "question": {
    "id": 16,
    "question_text": "What's the difference between let and const?",
    "status": "pending",
    "upvote_count": 0,
    "created_at": "2025-10-06T15:00:00Z",
    "attendee": {
      "display_name": "Anonymous",
      "is_anonymous": true
    }
  }
}
```
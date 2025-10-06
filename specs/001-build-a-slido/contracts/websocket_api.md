# WebSocket API Contract

**WebSocket URL**: `/ws/{event_slug}`  
**Protocol**: WebSocket over HTTP/HTTPS  
**Authentication**: Session-based for attendees, Host code for hosts

## Connection Establishment

### Attendee Connection
```
ws://localhost:8000/ws/js-advanced-2025?session_id=session_abc123def456&display_name=Sarah%20Chen
```

**Query Parameters**:
- `session_id`: Required, unique session identifier
- `display_name`: Optional, URL-encoded display name
- `reconnect_token`: Optional, for session recovery

### Host Connection
```  
ws://localhost:8000/ws/js-advanced-2025?host_code=host_9f8e7d6c5b4a
```

**Query Parameters**:
- `host_code`: Required for host connections
- `reconnect_token`: Optional, for session recovery

### Connection Response
```json
{
  "event_type": "connection_established",
  "role": "attendee",
  "event_id": 1,
  "session_id": "session_abc123def456",
  "reconnect_token": "reconnect_xyz789",
  "current_state": {
    "active_polls": [1, 3],
    "attendee_count": 24
  }
}
```

---

## Real-time Poll Updates

### Poll Opened
Broadcast to all participants when host opens a poll.

```json
{
  "event_type": "poll_opened",
  "poll": {
    "id": 2,
    "question_text": "Which topic should we cover next?",
    "poll_type": "single",
    "status": "open",
    "opened_at": "2025-10-06T14:50:00Z",
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
      }
    ]
  }
}
```

### Poll Results Update
Broadcast to all participants when votes are cast (real-time).

```json
{
  "event_type": "poll_results_updated",
  "poll_id": 2,
  "total_votes": 15,
  "options": [
    {
      "id": 5,
      "vote_count": 8,
      "percentage": 53.3
    },
    {
      "id": 6, 
      "vote_count": 7,
      "percentage": 46.7
    }
  ],
  "timestamp": "2025-10-06T14:52:30Z"
}
```

### Poll Closed
Broadcast to all participants when host closes a poll.

```json
{
  "event_type": "poll_closed",
  "poll_id": 2,
  "closed_at": "2025-10-06T15:00:00Z",
  "final_results": {
    "total_votes": 23,
    "options": [
      {
        "id": 5,
        "option_text": "Async/Await Patterns",
        "vote_count": 14,
        "percentage": 60.9
      },
      {
        "id": 6,
        "option_text": "Error Handling", 
        "vote_count": 9,
        "percentage": 39.1
      }
    ]
  }
}
```

---

## Real-time Question Updates

### Question Approved
Broadcast to all participants when host approves a question.

```json
{
  "event_type": "question_approved",
  "question": {
    "id": 15,
    "question_text": "How do you handle race conditions in React with useEffect?",
    "status": "approved",
    "upvote_count": 2,
    "created_at": "2025-10-06T14:55:00Z",
    "moderated_at": "2025-10-06T14:57:00Z",
    "attendee": {
      "display_name": "Sarah Chen",
      "is_anonymous": false
    }
  }
}
```

### Question Upvoted
Broadcast to all participants when question receives upvote.

```json
{
  "event_type": "question_upvoted",
  "question_id": 15,
  "new_upvote_count": 3,
  "timestamp": "2025-10-06T14:58:00Z"
}
```

### Question Queue Reordered
Broadcast when upvotes cause queue reordering.

```json
{
  "event_type": "question_queue_updated",
  "questions": [
    {
      "id": 12,
      "upvote_count": 8,
      "position": 1
    },
    {
      "id": 15,
      "upvote_count": 3, 
      "position": 2
    },
    {
      "id": 10,
      "upvote_count": 2,
      "position": 3
    }
  ],
  "timestamp": "2025-10-06T14:58:00Z"
}
```

### Question Rejected (Host Only)
Sent only to hosts when they reject a question.

```json
{
  "event_type": "question_rejected",
  "question_id": 16,
  "reason": "Off-topic for this session",
  "moderated_at": "2025-10-06T14:59:00Z"
}
```

---

## Attendee Management

### Attendee Joined
Broadcast to hosts when new attendee joins.

```json
{
  "event_type": "attendee_joined",
  "attendee": {
    "id": 25,
    "display_name": "Alex Thompson",
    "is_anonymous": false,
    "joined_at": "2025-10-06T15:02:00Z"
  },
  "total_attendee_count": 25
}
```

### Attendee Count Update
Broadcast to all participants periodically.

```json
{
  "event_type": "attendee_count_updated",
  "total_count": 25,
  "active_count": 23,
  "timestamp": "2025-10-06T15:05:00Z"
}
```

---

## Client-to-Server Messages

### Heartbeat
Keep connection alive and update last_active timestamp.

```json
{
  "action": "heartbeat",
  "timestamp": "2025-10-06T15:06:00Z"
}
```

### Subscribe to Updates
Request specific update types (optional filtering).

```json
{
  "action": "subscribe",
  "event_types": ["poll_results_updated", "question_upvoted"],
  "timestamp": "2025-10-06T15:06:00Z"
}
```

---

## Error Handling

### Connection Error
```json
{
  "event_type": "error",
  "error_code": "INVALID_SESSION",
  "message": "Session ID not found or expired",
  "timestamp": "2025-10-06T15:07:00Z"
}
```

### Rate Limiting
```json
{
  "event_type": "error", 
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests, please slow down",
  "retry_after": 30,
  "timestamp": "2025-10-06T15:07:00Z"
}
```

---

## Performance Requirements

- **Message Delivery**: <100ms from server event to client receipt
- **Connection Limit**: 1000 concurrent connections per event
- **Message Rate**: Max 10 messages/second per connection
- **Reconnection**: Automatic with exponential backoff
- **State Sync**: Full state sync on reconnection within 5 seconds
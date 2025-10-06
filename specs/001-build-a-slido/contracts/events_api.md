# Events API Contract

**Base URL**: `/api/v1/events`  
**Authentication**: Host code required for creation and management

## POST /api/v1/events
Create a new event.

### Request
```json
{
  "title": "Advanced JavaScript Workshop",
  "slug": "js-advanced-2025",
  "description": "Deep dive into async patterns and modern JS"
}
```

### Response (201 Created)
```json
{
  "id": 1,
  "title": "Advanced JavaScript Workshop", 
  "slug": "js-advanced-2025",
  "short_code": "ABC12345",
  "host_code": "host_9f8e7d6c5b4a",
  "description": "Deep dive into async patterns and modern JS",
  "created_at": "2025-10-06T14:30:00Z",
  "is_active": true,
  "attendee_count": 0
}
```

### Validation Rules
- `title`: Required, 1-200 characters
- `slug`: Required, 3-50 characters, alphanumeric + hyphens, must be unique
- `description`: Optional, max 1000 characters

---

## GET /api/v1/events/{slug}
Get event details for attendee joining.

### Response (200 OK)
```json
{
  "id": 1,
  "title": "Advanced JavaScript Workshop",
  "slug": "js-advanced-2025", 
  "description": "Deep dive into async patterns and modern JS",
  "is_active": true,
  "attendee_count": 23
}
```

### Error Response (404 Not Found)
```json
{
  "error": "Event not found",
  "code": "EVENT_NOT_FOUND"
}
```

---

## GET /api/v1/events/{slug}/host
Get host dashboard data (requires host_code).

### Headers
```
Authorization: Host host_9f8e7d6c5b4a
```

### Response (200 OK)
```json
{
  "event": {
    "id": 1,
    "title": "Advanced JavaScript Workshop",
    "slug": "js-advanced-2025",
    "created_at": "2025-10-06T14:30:00Z",
    "is_active": true
  },
  "polls": [
    {
      "id": 1,
      "question_text": "What's your JavaScript experience?",
      "status": "open",
      "poll_type": "single", 
      "total_votes": 18,
      "options": [
        {
          "id": 1,
          "option_text": "Beginner",
          "vote_count": 5,
          "percentage": 27.8
        },
        {
          "id": 2,
          "option_text": "Intermediate", 
          "vote_count": 10,
          "percentage": 55.6
        },
        {
          "id": 3,
          "option_text": "Advanced",
          "vote_count": 3,
          "percentage": 16.7
        }
      ]
    }
  ],
  "questions": [
    {
      "id": 1,
      "question_text": "How do async/await differ from promises?",
      "status": "pending",
      "upvote_count": 5,
      "created_at": "2025-10-06T14:35:00Z",
      "attendee": {
        "display_name": "Sarah Chen",
        "is_anonymous": false
      }
    }
  ],
  "attendees": {
    "total_count": 23,
    "active_count": 21,
    "anonymous_count": 8
  }
}
```

### Error Response (401 Unauthorized)
```json
{
  "error": "Invalid host code",
  "code": "UNAUTHORIZED_HOST"
}
```

---

## PUT /api/v1/events/{slug}/status
Update event active status (requires host_code).

### Headers
```
Authorization: Host host_9f8e7d6c5b4a
```

### Request
```json
{
  "is_active": false
}
```

### Response (200 OK)
```json
{
  "id": 1,
  "is_active": false,
  "updated_at": "2025-10-06T16:00:00Z"
}
```
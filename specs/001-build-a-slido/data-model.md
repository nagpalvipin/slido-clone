# Data Model: Live Q&A & Polls Application

**Date**: 2025-10-06  
**Feature**: 001-build-a-slido  
**Database**: SQLite with SQLAlchemy ORM

## Entity Relationship Overview

```
Event (1) ────── (N) Poll (1) ────── (N) PollOption (1) ────── (N) PollResponse
  │                                                                    │
  │                                                                    │
  └─── (N) Question (1) ────── (N) QuestionVote                      │
                │                                                      │
                └────── (N) Attendee ──────────────────────────────────┘
```

## Core Entities

### Event
Primary entity representing a course session or presentation.

**Attributes**:
- `id`: Integer, Primary Key, Auto-increment
- `title`: String(200), Required - Display name for the event
- `slug`: String(50), Unique, Required - URL-friendly identifier for attendee access
- `short_code`: String(8), Unique, Required - Generated code for easy joining
- `host_code`: String(20), Required - Authentication code for host access
- `created_at`: DateTime, Auto-generated
- `is_active`: Boolean, Default True - Controls whether new attendees can join
- `description`: Text, Optional - Additional event context

**Validation Rules**:
- Slug must be lowercase alphanumeric with hyphens only
- Short code must be exactly 8 characters, alphanumeric, case-insensitive
- Host code must be at least 12 characters for security

**Indexes**: `slug`, `short_code`, `host_code`

---

### Poll
Represents a single poll within an event (single-choice or multi-choice).

**Attributes**:
- `id`: Integer, Primary Key, Auto-increment
- `event_id`: Integer, Foreign Key → Event.id, Required
- `question_text`: Text, Required - The poll question
- `poll_type`: Enum('single', 'multi'), Required - Choice restriction
- `status`: Enum('draft', 'open', 'closed'), Default 'draft'
- `created_at`: DateTime, Auto-generated
- `opened_at`: DateTime, Nullable - When poll was opened for voting
- `closed_at`: DateTime, Nullable - When poll was closed
- `allow_anonymous`: Boolean, Default True

**Business Rules**:
- Polls can only be opened/closed by event hosts
- Vote counting only occurs for 'open' status polls
- Multi-choice polls allow multiple option selection per attendee
- Single-choice polls enforce one selection per attendee

**Relationships**:
- Belongs to Event (Many-to-One)
- Has many PollOptions (One-to-Many)

**Indexes**: `event_id`, `status`

---

### PollOption
Individual answer choices within a poll.

**Attributes**:
- `id`: Integer, Primary Key, Auto-increment
- `poll_id`: Integer, Foreign Key → Poll.id, Required
- `option_text`: String(500), Required - The answer choice text
- `position`: Integer, Required - Display order (0-based)
- `vote_count`: Integer, Default 0 - Cached count for performance

**Business Rules**:
- Position determines display order in UI
- Vote count is maintained for real-time display efficiency
- Minimum 2 options per poll, maximum 10 options

**Relationships**:
- Belongs to Poll (Many-to-One)
- Has many PollResponses (One-to-Many)

**Indexes**: `poll_id`, `position`

---

### PollResponse
Records individual attendee votes on poll options.

**Attributes**:
- `id`: Integer, Primary Key, Auto-increment
- `poll_id`: Integer, Foreign Key → Poll.id, Required
- `option_id`: Integer, Foreign Key → PollOption.id, Required
- `attendee_id`: Integer, Foreign Key → Attendee.id, Required
- `created_at`: DateTime, Auto-generated

**Business Rules**:
- Composite unique constraint: (poll_id, attendee_id, option_id) for multi-choice
- For single-choice polls: only one response per (poll_id, attendee_id)
- Responses are immutable once created
- Cascade delete when poll or attendee is removed

**Relationships**:
- Belongs to Poll (Many-to-One)
- Belongs to PollOption (Many-to-One)
- Belongs to Attendee (Many-to-One)

**Indexes**: `poll_id`, `attendee_id`, `option_id`

---

### Question
Attendee-submitted questions for the moderated Q&A queue.

**Attributes**:
- `id`: Integer, Primary Key, Auto-increment
- `event_id`: Integer, Foreign Key → Event.id, Required
- `attendee_id`: Integer, Foreign Key → Attendee.id, Required
- `question_text`: Text, Required - The submitted question
- `status`: Enum('pending', 'approved', 'rejected'), Default 'pending'
- `upvote_count`: Integer, Default 0 - Cached count for queue ordering
- `created_at`: DateTime, Auto-generated
- `moderated_at`: DateTime, Nullable - When host approved/rejected
- `is_answered`: Boolean, Default False - Host can mark as answered

**Business Rules**:
- Questions start as 'pending' and require host moderation
- Only 'approved' questions are visible to attendees
- Queue ordering by upvote_count DESC, then created_at ASC
- Maximum 1000 characters per question
- Attendees can submit maximum 5 questions per event

**Relationships**:
- Belongs to Event (Many-to-One)
- Belongs to Attendee (Many-to-One)
- Has many QuestionVotes (One-to-Many)

**Indexes**: `event_id`, `status`, `upvote_count DESC`, `created_at`

---

### QuestionVote
Records upvotes on questions by attendees.

**Attributes**:
- `id`: Integer, Primary Key, Auto-increment
- `question_id`: Integer, Foreign Key → Question.id, Required
- `attendee_id`: Integer, Foreign Key → Attendee.id, Required
- `created_at`: DateTime, Auto-generated

**Business Rules**:
- Composite unique constraint: (question_id, attendee_id) - no duplicate votes
- Attendees can upvote multiple questions but only once per question
- Upvotes are permanent (no removal/downvote functionality)
- Cascade delete when question or attendee is removed

**Relationships**:
- Belongs to Question (Many-to-One)
- Belongs to Attendee (Many-to-One)

**Indexes**: `question_id`, `attendee_id`

---

### Attendee
Represents a session participant (anonymous or named).

**Attributes**:
- `id`: Integer, Primary Key, Auto-increment
- `event_id`: Integer, Foreign Key → Event.id, Required
- `session_id`: String(64), Required - Browser/client session identifier
- `display_name`: String(50), Nullable - Optional user-provided name
- `is_anonymous`: Boolean, Default True
- `joined_at`: DateTime, Auto-generated
- `last_active`: DateTime, Auto-updated on activity

**Business Rules**:
- Session ID uniquely identifies attendee within event
- Display name is optional but if provided must be event-unique
- Anonymous attendees show as "Anonymous User" in UI
- Inactive attendees (no activity >30 minutes) excluded from active counts

**Relationships**:
- Belongs to Event (Many-to-One)
- Has many PollResponses (One-to-Many)
- Has many Questions (One-to-Many)
- Has many QuestionVotes (One-to-Many)

**Indexes**: `event_id`, `session_id`, `last_active`

---

## Performance Considerations

### Query Optimization
- **Real-time vote counting**: PollOption.vote_count cached field updated via triggers
- **Question queue ordering**: Composite index on (event_id, status, upvote_count DESC)
- **Active attendee counts**: Filter by last_active within 30 minutes

### Concurrency Handling
- **Optimistic locking**: Version fields on critical entities (Poll, Question)
- **Atomic updates**: Database transactions for vote operations
- **Cache invalidation**: WebSocket broadcasts trigger client cache updates

### Data Retention
- **Event lifecycle**: Events remain active until host deactivation
- **Anonymous cleanup**: Remove attendee records after 7 days of inactivity
- **Archive strategy**: Move closed events to archive tables after 30 days

---

**Model Complete**: All entities defined with relationships, constraints, and performance considerations aligned with constitutional requirements for real-time updates and data integrity.
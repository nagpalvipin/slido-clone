# Data Model: Fix Critical UX Issues

## Overview
Data model updates and clarifications for implementing 5 critical UX fixes. Most entities already exist; this document focuses on modifications and relationship clarifications.

## Entity Modifications

### Event Entity (Existing - Modified)
**Purpose**: Represents a live or scheduled event where attendees participate

**Existing Fields**:
- `id`: INTEGER, Primary Key, Auto-increment
- `title`: VARCHAR(200), NOT NULL
- `slug`: VARCHAR(50), UNIQUE, NOT NULL
- `description`: TEXT, NULLABLE
- `short_code`: VARCHAR(20), UNIQUE, NOT NULL (attendee access)
- `host_code`: VARCHAR(50), UNIQUE, NOT NULL (host access)
- `is_active`: BOOLEAN, DEFAULT TRUE
- `created_at`: TIMESTAMP, DEFAULT NOW()

**Modifications**:
- **host_code field**: Already exists with UNIQUE constraint ✓
  - Pattern: `host_[a-z0-9]{12}` (validated in application layer)
  - Can be custom (user-provided) or auto-generated
  - Database enforces uniqueness to prevent concurrent creation conflicts
  
**New Validations** (Application Layer):
- Custom host_code must match regex: `^host_[a-z0-9]{12}$`
- Minimum length: 17 characters (`host_` + 12 chars)
- Case-insensitive uniqueness check before DB insert
- Sanitization: lowercase, strip whitespace

**Relationships**:
- ONE-TO-MANY with `Question` (event.questions)
- ONE-TO-MANY with `Poll` (event.polls)
- ONE-TO-MANY with `Attendee` (event.attendees)
- Implicit: Multiple events can share same host (via host_code pattern, but each event has unique code)

**Indexes** (Performance):
- `idx_event_host_code` on `host_code` (UNIQUE INDEX - already exists via constraint)
- `idx_event_created_at` on `created_at` DESC (for pagination)
- Composite: `idx_host_event_created` on `(host_code, created_at DESC)` (NEW - for host event list)

### Question Entity (Existing - No Schema Changes)
**Purpose**: Question submitted by attendee during event

**Schema** (Unchanged):
- `id`: INTEGER, Primary Key
- `event_id`: INTEGER, Foreign Key → events.id, NOT NULL
- `attendee_id`: INTEGER, Foreign Key → attendees.id, NOT NULL
- `question_text`: TEXT, NOT NULL (1-1000 chars validated in app)
- `status`: ENUM('submitted', 'approved', 'answered', 'rejected'), DEFAULT 'submitted'
- `created_at`: TIMESTAMP, DEFAULT NOW()

**Computed Properties** (Application Layer):
- `upvote_count`: Derived from COUNT(question_votes) where question_id = this.id
  - **CRITICAL**: Cannot be used in SQL ORDER BY directly
  - Must use subquery with JOIN for sorting by votes

**Relationships**:
- MANY-TO-ONE with `Event` (question.event)
- MANY-TO-ONE with `Attendee` (question.attendee)
- ONE-TO-MANY with `QuestionVote` (question.votes)

**Query Pattern Fix** (Already Implemented):
```python
# BROKEN (property in ORDER BY):
db.query(Question).order_by(Question.upvote_count.desc())  # ❌ AttributeError

# FIXED (subquery for vote count):
vote_subquery = db.query(
    QuestionVote.question_id,
    func.count(QuestionVote.id).label('vote_count')
).group_by(QuestionVote.question_id).subquery()

questions = db.query(Question).outerjoin(
    vote_subquery,
    Question.id == vote_subquery.c.question_id
).order_by(
    vote_subquery.c.vote_count.desc().nullslast(),
    Question.created_at.asc()
).all()  # ✓ Correct
```

### QuestionVote Entity (Existing - No Changes)
**Purpose**: Tracks upvotes on questions by attendees

**Schema**:
- `id`: INTEGER, Primary Key
- `question_id`: INTEGER, Foreign Key → questions.id, NOT NULL
- `attendee_id`: INTEGER, Foreign Key → attendees.id, NOT NULL
- `created_at`: TIMESTAMP, DEFAULT NOW()
- **Constraint**: UNIQUE(question_id, attendee_id) - one vote per attendee per question

**Relationships**:
- MANY-TO-ONE with `Question`
- MANY-TO-ONE with `Attendee`

### Attendee Entity (Existing - No Changes)
**Purpose**: Represents event participant (anonymous, session-based)

**Schema**:
- `id`: INTEGER, Primary Key
- `event_id`: INTEGER, Foreign Key → events.id, NOT NULL
- `session_id`: VARCHAR(100), NOT NULL (UUID or similar)
- `created_at`: TIMESTAMP, DEFAULT NOW()
- **Constraint**: UNIQUE(event_id, session_id)

**Relationships**:
- MANY-TO-ONE with `Event`
- ONE-TO-MANY with `Question`
- ONE-TO-MANY with `QuestionVote`

## New API Response Models

### PaginatedEventsResponse
**Purpose**: Response for host's event list with pagination

```typescript
interface PaginatedEventsResponse {
  events: EventSummary[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

interface EventSummary {
  id: number;
  title: string;
  slug: string;
  short_code: string;  // For attendees
  created_at: string;  // ISO 8601
  is_active: boolean;
  question_count?: number;  // Optional: computed
  poll_count?: number;      // Optional: computed
}
```

**Backend Implementation**:
```python
class EventSummaryResponse(BaseModel):
    id: int
    title: str
    slug: str
    short_code: str
    created_at: datetime
    is_active: bool
    question_count: int = 0
    poll_count: int = 0

class PaginatedEventsResponse(BaseModel):
    events: List[EventSummaryResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
```

### EventCreateRequest (Modified)
**Purpose**: Request payload for creating new event

```python
class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    host_code: Optional[str] = Field(None, min_length=17, max_length=50)  # NEW
    
    @validator('host_code')
    def validate_host_code_format(cls, v):
        if v and not re.match(r'^host_[a-z0-9]{12}$', v):
            raise ValueError('Invalid host code format. Must be: host_xxxxxxxxxxxxx')
        return v.lower() if v else None
```

### EventCreateResponse (Modified)
**Purpose**: Response after creating event

```python
class EventCreateResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: Optional[str]
    short_code: str        # For sharing with attendees
    host_code: str         # For host access (custom or generated)
    created_at: datetime
    is_active: bool
    attendee_count: int = 0
```

## State Transitions

### Question Status Flow
```
[submitted] → (host moderates) → [approved | rejected]
[approved]  → (host answers)   → [answered]
```

**Rules**:
- Default status: `submitted`
- Only host can change status
- `rejected` questions hidden from attendee view
- `answered` questions marked with visual indicator

### Event Lifecycle
```
[created] → (is_active=true) → [active]
[active]  → (host ends)      → [inactive] (is_active=false)
```

**Persistence**:
- Events never deleted (audit trail)
- Inactive events: read-only for attendees
- Inactive events: still manageable by host (view results)

## Data Validation Rules

### Input Validation (Application Layer)

**Event Creation**:
- `title`: 1-200 chars, required, strip whitespace
- `slug`: 3-50 chars, lowercase, alphanumeric + hyphens, unique
- `description`: 0-1000 chars, optional
- `host_code`: 17-50 chars (if provided), match pattern, unique check

**Question Submission**:
- `question_text`: 1-1000 chars, required, strip leading/trailing whitespace
- Internal whitespace preserved (multiline questions allowed)
- No HTML/script injection (sanitized on render)

**Host Code**:
- Auto-generated: `host_` + 12 random lowercase alphanumeric
- Custom: Must start with `host_`, followed by exactly 12 [a-z0-9]
- Uniqueness: Database constraint enforces, app checks before insert

### Database Constraints

**UNIQUE Constraints**:
- `events.slug` - One event per slug
- `events.short_code` - One event per attendee code
- `events.host_code` - One event per host code (prevents duplicates)
- `(attendees.event_id, attendees.session_id)` - One session per event
- `(question_votes.question_id, question_votes.attendee_id)` - One vote per question per attendee

**FOREIGN KEY Constraints**:
- `questions.event_id` → `events.id` ON DELETE CASCADE
- `questions.attendee_id` → `attendees.id` ON DELETE CASCADE
- `question_votes.question_id` → `questions.id` ON DELETE CASCADE
- `question_votes.attendee_id` → `attendees.id` ON DELETE CASCADE

**CHECK Constraints** (if supported):
- `LENGTH(questions.question_text) <= 1000`
- `LENGTH(events.title) <= 200`

## Query Optimization

### Indexes for Performance

**Existing Indexes** (Assumed):
- Primary keys: `id` on all tables (clustered)
- Unique constraints create indexes automatically

**New Indexes Required**:
```sql
-- Host event list (pagination)
CREATE INDEX idx_host_event_created ON events(host_code, created_at DESC);

-- Question sorting by votes (alternative to subquery)
CREATE INDEX idx_question_event_created ON questions(event_id, created_at ASC);

-- Vote counting
CREATE INDEX idx_vote_question ON question_votes(question_id);
```

### Query Patterns

**Host Event List** (Optimized):
```python
# With pagination and counts
events = db.query(
    Event,
    func.count(Question.id).label('question_count')
).outerjoin(Question).filter(
    Event.host_code == host_code
).group_by(Event.id).order_by(
    Event.created_at.desc()
).offset((page - 1) * per_page).limit(per_page).all()
```

**Questions with Vote Counts** (Fixed):
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

## Data Migration

### Alembic Migration (If Needed)
**Scenario**: If host_code field needs modification (unlikely - already exists correctly)

```python
# alembic/versions/xxx_add_host_event_index.py
def upgrade():
    # Add composite index for host event pagination
    op.create_index(
        'idx_host_event_created',
        'events',
        ['host_code', sa.text('created_at DESC')]
    )
    
def downgrade():
    op.drop_index('idx_host_event_created', 'events')
```

### Data Consistency Checks
**Pre-deployment verification**:
1. Ensure all existing events have valid host_codes
2. Verify UNIQUE constraint on host_code exists
3. Check for orphaned questions/votes (cleanup if any)

## Performance Considerations

### Scalability Limits
- **Events per host**: Unlimited, paginated (20 per page)
- **Questions per event**: 1000+ supported with indexed queries
- **Concurrent submissions**: Database handles via transactions
- **Real-time updates**: WebSocket broadcast to max 1000 clients per event

### Caching Strategy
- **Event list**: Client-side cache, 5-minute TTL
- **Question list**: Real-time, no caching (WebSocket updates)
- **Vote counts**: Computed on-demand (subquery), no denormalization

### Query Performance Targets
- Event list query: <50ms (indexed on host_code + created_at)
- Questions query: <200ms (subquery join optimized)
- Vote counting: <100ms (indexed foreign keys)
- Event creation: <100ms (single INSERT with unique check)

## Security Considerations

### Data Protection
- **Host codes**: Treated as sensitive credentials
  - Never logged in plain text
  - Transmitted over HTTPS only
  - Validated server-side (frontend validation is UX only)

- **Question content**: User-generated, potential XSS
  - Sanitized on display (React auto-escapes)
  - No HTML rendering in question text
  - Length limits enforced (DoS prevention)

### Authorization
- **Event access**: Host code required for management endpoints
- **Question submission**: Anonymous (session-based), rate-limited
- **Question voting**: One vote per session per question (DB constraint)

### Audit Trail
- **created_at timestamps**: Immutable, server-controlled
- **Event lifecycle**: is_active flag for soft delete
- **Question history**: Status changes logged (future: add updated_at + updated_by)

## Frontend State Shape

### EventSwitcher Component State
```typescript
interface EventSwitcherState {
  events: EventSummary[];
  currentEventId: number | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    page: number;
    perPage: number;
    total: number;
    totalPages: number;
  };
  searchQuery: string;
}
```

### HostDashboard Component State
```typescript
interface HostDashboardState {
  event: EventHostView | null;
  hostCode: string;
  questions: Question[];
  polls: Poll[];
  isLoading: boolean;
  error: string | null;
}
```

### Question Submission State
```typescript
interface QuestionFormState {
  questionText: string;
  isSubmitting: boolean;
  error: string | null;
  recentlySubmitted: number[]; // IDs for highlight animation
}
```

## Data Flow Diagrams

### Question Submission Flow
```
Attendee Input → Validation → API Request → Backend Service →
Database Insert → WebSocket Broadcast → Host Dashboard Update
                                      ↓
                              Attendee UI Update (optimistic)
```

### Event Creation Flow
```
Host Input (optional custom code) → Validation → Uniqueness Check →
Generate/Use Code → Database Insert → Return Event with Codes →
Store in EventSwitcher → Navigate to Dashboard
```

### Multi-Event Navigation
```
Load Dashboard → Fetch Event List (paginated) → Display Switcher →
User Selects → Update URL → Fetch Event Data → Update Dashboard
```

## Testing Data

### Seed Data for Tests
```python
# Contract test fixtures
VALID_HOST_CODE = "host_abc123xyz789"
INVALID_HOST_CODE_TOO_SHORT = "host_abc"
INVALID_HOST_CODE_BAD_CHARS = "host_ABC-123-XYZ"
DUPLICATE_HOST_CODE = "host_existing123"

# Test event
test_event = {
    "title": "Test Event",
    "slug": "test-event-001",
    "description": "Test description",
    "host_code": VALID_HOST_CODE
}

# Test question
test_question = {
    "question_text": "What is the meaning of life?",
    "event_id": 1,
    "attendee_id": 1
}
```

### Edge Case Data
- Empty question text: ""
- Maximum length question: "A" * 1000
- Special characters in question: "Question with <script>alert('xss')</script>"
- Unicode question: "Вопрос на русском языке?"
- 1000+ votes on single question
- 100+ events for single host

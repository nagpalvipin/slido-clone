# Research: Fix Critical UX Issues

## Overview
Research findings for implementing 5 critical UX fixes in Slido Clone application. Focus on identifying root causes, technical solutions, and best practices for each issue.

## Issue 1: Attendee Question Submission Not Working

### Root Cause Analysis
**Decision**: Backend SQL query bug in `QuestionService.get_questions_for_event()` 
- Attempting to use `Question.upvote_count.desc()` in ORDER BY clause
- `upvote_count` is a Python `@property` that counts related `QuestionVote` records
- Cannot be used directly in SQLAlchemy query ordering

**Rationale**: 
- Properties are computed at runtime, not database columns
- SQL requires actual columns or subqueries for ORDER BY
- Error manifests as AttributeError: 'property' object has no attribute 'desc'

**Solution Implemented**:
- Replace property-based ordering with SQL subquery
- Create vote count subquery using `func.count()` and `GROUP BY`
- Use `outerjoin()` to handle questions with zero votes
- Apply `.nullslast()` to ensure zero-vote questions appear last

**Alternatives Considered**:
1. Add `upvote_count` as database column - Rejected: introduces data denormalization and sync issues
2. Load all questions and sort in Python - Rejected: performance issue at scale
3. Use hybrid_property with expression - Rejected: adds complexity for minimal benefit

### Frontend Integration
**Decision**: Question submission API already correctly implemented
- AttendeeInterface.tsx calls `api.questions.create()`  
- Real-time hooks (`useQuestionsState`) handle WebSocket updates
- Visual feedback needed: highlight animation on new question

**Best Practices**:
- Optimistic UI updates for perceived performance
- Error boundary for graceful failure handling
- Debounce rapid submissions (300ms) to prevent spam

## Issue 2: Host Dashboard Not Displaying Questions

### Root Cause Analysis
**Decision**: Same SQL query bug affects host question retrieval
- GET `/api/v1/events/{event_id}/questions` endpoint uses same service method
- Returns 500 Internal Server Error due to property ordering issue
- Authentication works correctly (host code validation functional)

**Solution**:
- Fix applies to both `get_questions_for_event()` and `get_questions_for_moderation()`
- Both methods need subquery-based vote counting
- Maintain ordering: votes DESC (high to low), then created_at ASC (oldest first)

**Verification Strategy**:
- Contract tests: Assert 200 response with correct JSON schema
- Integration tests: Submit question as attendee, verify host sees it
- Real-time tests: Validate WebSocket message delivery within 2s

## Issue 3: Custom Host Code Selection

### Technical Approach
**Decision**: Add optional `custom_host_code` field to event creation endpoint
- Modify POST `/api/v1/events` to accept `host_code` in request body (optional)
- Validate format: alphanumeric, 12+ chars, matches pattern `host_[a-z0-9]{12}`
- Check uniqueness via database constraint (Event.host_code UNIQUE)
- Fallback to auto-generation if not provided

**Rationale**:
- Maintains backward compatibility (optional field)
- Database-level uniqueness prevents race conditions
- Security validation prevents injection attacks

**Implementation Details**:
```python
# EventCreateRequest schema update
class EventCreateRequest(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    host_code: Optional[str] = None  # NEW FIELD
    
# Validation logic
if custom_host_code:
    if not SecurityUtils.validate_host_code(custom_host_code):
        raise HTTPException(422, "Invalid host code format")
    if db.query(Event).filter(Event.host_code == custom_host_code).first():
        raise HTTPException(409, "Host code already in use")
    event.host_code = custom_host_code
else:
    event.host_code = SecurityUtils.generate_host_code()
```

**Frontend Form Design**:
- Add collapsible "Advanced Options" section
- Input field with format helper text: "Format: host_xxxxxxxxxxxxx"
- Real-time validation with debounce (500ms)
- Show availability status (✓ Available / ✗ Already taken)

**Best Practices**:
- Case-insensitive comparison for uniqueness check
- Sanitize input (strip whitespace, lowercase)
- Clear error messaging with actionable suggestions

## Issue 4: Host Code Display on Dashboard

### UX Design Pattern
**Decision**: Prominent header section with copy-to-clipboard functionality
- Position: Top of HostDashboard, always visible (sticky header)
- Visual hierarchy: Large code in monospace font, contrasting background
- Copy button with icon + text: "📋 Copy Host Code"
- Success feedback: Button text changes to "✓ Copied!" for 2s

**Component Structure**:
```tsx
<div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border-2 border-indigo-200">
  <div className="flex items-center justify-between">
    <div>
      <label className="text-sm font-medium text-gray-600">Your Host Code</label>
      <code className="block text-2xl font-mono font-bold text-indigo-900">
        {hostCode}
      </code>
    </div>
    <button onClick={handleCopy} className="btn-primary">
      {copied ? '✓ Copied!' : '📋 Copy'}
    </button>
  </div>
  <p className="text-sm text-gray-600 mt-2">
    Share this code with co-hosts to grant them access to manage this event.
  </p>
</div>
```

**Accessibility Considerations**:
- Aria-label for copy button: "Copy host code to clipboard"
- Announce copy success to screen readers
- Keyboard accessible (Enter/Space to copy)
- High contrast for WCAG AA compliance

**Best Practices**:
- Use Clipboard API with fallback for older browsers
- Handle permission denied gracefully
- Visual feedback duration: 2000ms (research-backed optimal duration)

## Issue 5: Multi-Event Creation & Navigation

### Architecture Decision
**Decision**: Event switcher dropdown with pagination support
- Component: `<EventSwitcher />` - Reusable dropdown component
- Data fetching: New endpoint GET `/api/v1/events/host` (returns host's events)
- Pagination: Server-side, 20 events per page, cursor-based navigation
- UI Pattern: Dropdown with search/filter, "Create New Event" button always visible

**Implementation Strategy**:

**Backend - New Endpoint**:
```python
@router.get("/host", response_model=PaginatedEventsResponse)
async def get_host_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    host_code = SecurityUtils.extract_host_code_from_header(authorization)
    
    # Query events where this host_code matches
    query = db.query(Event).filter(Event.host_code == host_code)
    total = query.count()
    
    events = query.order_by(Event.created_at.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()
    
    return {
        "events": events,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }
```

**Frontend - EventSwitcher Component**:
- Headless UI Listbox for accessible dropdown
- Virtual scrolling for 100+ events (react-window)
- Debounced search filter (300ms)
- "Create New Event" modal trigger at top

**State Management**:
- Store current event ID in localStorage for persistence
- Update on dropdown selection
- Sync across tabs using storage event listener

**Best Practices**:
- Infinite scroll alternative: Load more on scroll to bottom
- Cache event list with 5-minute TTL
- Optimistic UI for event creation (add to list immediately)
- Show loading skeleton during fetch

### Navigation Flow
1. Host lands on dashboard → Load default event (most recent or localStorage)
2. Click event switcher → Dropdown opens with paginated list
3. Type to search → Filter events by title/slug (client-side first 20, then server-side)
4. Select event → Update URL, fetch event data, update dashboard
5. Click "Create New" → Open modal, submit, add to list, switch to new event

**Performance Optimizations**:
- Prefetch next page on hover over pagination controls
- Memoize event list to prevent unnecessary re-renders
- Use SWR (stale-while-revalidate) for background updates

## Cross-Cutting Concerns

### Real-Time Updates
**Decision**: Maintain existing WebSocket infrastructure
- Questions: Already broadcast on `question_created` event
- Events: Add `event_updated` for host code changes (future)
- Connection resilience: Auto-reconnect with exponential backoff

### Error Handling
**Standard Error Patterns**:
- 400 Bad Request: Invalid input (show field-specific errors)
- 401 Unauthorized: Invalid host code (redirect to login)
- 409 Conflict: Duplicate host code/slug (suggest alternatives)
- 500 Internal Server Error: Log and show generic message

**User-Facing Messages**:
- Technical errors → "Something went wrong. Please try again."
- Validation errors → Field-specific actionable guidance
- Success states → Brief confirmation (2s toast)

### Testing Strategy
**Contract Tests** (Phase 1 - Write First):
- POST /events with custom host_code (200, 409, 422)
- GET /events/{id}/questions with auth (200, 401)
- GET /events/host with pagination (200, validate schema)

**Integration Tests** (Phase 1 - Write First):
- End-to-end question submission flow
- Host code uniqueness enforcement
- Multi-event creation and switching

**Unit Tests**:
- SecurityUtils.validate_host_code() edge cases
- QuestionService vote counting logic
- EventSwitcher pagination logic

### Performance Benchmarks
**Target Metrics** (from spec):
- Question submission: <500ms (backend + network)
- Real-time update delivery: <2s (WebSocket latency)
- Database queries: <200ms p95 (indexed queries)
- Event switcher load: <300ms (20 events)

**Measurement Plan**:
- Backend: Python `time.perf_counter()` for route timing
- Frontend: Performance API (`performance.mark()`)
- Database: SQLAlchemy query logging with duration
- Real-time: WebSocket event timestamps (client → server → broadcast → client)

## Technology Stack Decisions

### Confirmed Technologies
- **Backend Framework**: FastAPI (async, WebSocket support, OpenAPI)
- **ORM**: SQLAlchemy (async support, migration via Alembic)
- **Database**: SQLite (dev), PostgreSQL (prod) - both support UNIQUE constraints
- **Frontend Framework**: React 18 (hooks, concurrent features)
- **State Management**: React hooks + Context (lightweight, no Redux needed)
- **Styling**: Tailwind CSS (utility-first, existing design system)
- **Real-Time**: WebSocket (native browser support, fallback to polling)
- **Testing**: pytest (backend), Vitest + RTL (frontend)

### No Additional Dependencies Required
All functionality achievable with existing stack. No new libraries needed.

## Risk Mitigation

### Identified Risks
1. **Database Lock Contention**: Multiple hosts creating events simultaneously
   - Mitigation: Database-level UNIQUE constraint handles atomically
   - Fallback: Retry logic with exponential backoff (3 attempts)

2. **WebSocket Connection Drops**: Real-time updates fail
   - Mitigation: Polling fallback (5s interval) if WebSocket unavailable
   - Auto-reconnect with connection state indicator

3. **Pagination Performance**: 1000+ events per host
   - Mitigation: Indexed queries on created_at + host_code
   - Consider event archival after 6 months

4. **Race Condition**: Host code validation check vs. creation
   - Mitigation: Database constraint is final authority
   - Frontend validation is UX enhancement, not security

## Implementation Sequence

### Phase 0: ✅ Research Complete
- Root causes identified for all 5 issues
- Technical solutions designed
- Best practices researched and documented

### Phase 1: Design & Contracts (Next)
- Generate API contract specifications
- Create data model updates
- Write failing contract tests
- Build quickstart validation scenarios

### Phase 2: Task Breakdown (After Phase 1)
- Ordered, parallel-safe task list
- TDD sequence: tests first, then implementation
- Dependency-aware ordering

## References

### Documentation
- FastAPI WebSocket: https://fastapi.tiangolo.com/advanced/websockets/
- SQLAlchemy Subqueries: https://docs.sqlalchemy.org/en/20/core/selectable.html
- React Clipboard API: https://developer.mozilla.org/en-US/docs/Web/API/Clipboard
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/

### Existing Codebase
- backend/src/services/question_service.py (line 139-148) - Bug location
- backend/src/api/events.py - Event creation endpoint
- frontend/src/components/AttendeeInterface.tsx - Question submission form
- frontend/src/components/HostDashboard.tsx - Dashboard needing enhancements

### Performance Research
- Optimal toast duration: 2000ms (Nielsen Norman Group)
- Debounce timing: 300-500ms (industry standard for search)
- WebSocket reconnect: Exponential backoff starting 1s, max 30s

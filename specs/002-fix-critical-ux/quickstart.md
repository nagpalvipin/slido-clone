# Quickstart: Critical UX Fixes Validation

## Overview
This guide provides end-to-end validation scenarios for the 5 critical UX fixes:
1. ✅ Attendee question submission
2. ✅ Host question visibility  
3. ✅ Custom host code option
4. ✅ Host code display on dashboard
5. ✅ Multi-event creation for hosts

## Prerequisites

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload --port 8001
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Runs on port 3000
```

### Verify Services
```bash
# Backend health check
curl http://localhost:8001/health

# Frontend
open http://localhost:3000
```

## Validation Scenario 1: Attendee Question Submission

### Test Case 1.1: Submit Question via UI

**Steps**:
1. Open http://localhost:3000/event/ABC123 (use existing event short code)
2. Enter question text: "What is the product roadmap for Q1 2025?"
3. Leave "Submit anonymously" unchecked
4. Click "Submit Question"

**Expected Result**:
- ✅ Success toast appears: "Question submitted successfully!"
- ✅ Question appears in questions list with highlight animation (yellow glow fading over 2s)
- ✅ Question shows 0 upvotes
- ✅ Question form clears

**Validation**:
```bash
# Verify question persisted in database
sqlite3 slido_clone.db "SELECT id, text, upvote_count FROM questions ORDER BY id DESC LIMIT 1;"
# Should show your question with upvote_count = 0
```

### Test Case 1.2: Submit Anonymous Question

**Steps**:
1. Enter question text: "How do you handle work-life balance?"
2. Check "Submit anonymously"
3. Click "Submit Question"

**Expected Result**:
- ✅ Question appears with author name as "Anonymous"
- ✅ No name/identifier shown

### Test Case 1.3: Validation Errors

**Test Empty Text**:
1. Leave question field empty
2. Click "Submit Question"
3. **Expected**: Error message "Question must be between 1 and 1000 characters"

**Test Text Too Long**:
1. Enter 1001 characters (copy-paste lorem ipsum)
2. Click "Submit Question"
3. **Expected**: Error message "Question must be between 1 and 1000 characters"

**Test Rate Limiting**:
1. Submit 10 questions in rapid succession
2. Try to submit 11th question within 1 minute
3. **Expected**: Error message "Rate limit exceeded. Please wait before submitting again."

### Test Case 1.4: Direct API Testing

```bash
# Get event ID (replace ABC123 with your short code)
EVENT_ID=$(sqlite3 slido_clone.db "SELECT id FROM events WHERE short_code='ABC123';")

# Submit question via API
curl -X POST http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Content-Type: application/json" \
  -H "Authorization: Attendee attendee_test_$(date +%s)" \
  -d '{
    "text": "API test question: How does the new feature work?",
    "is_anonymous": false
  }' | jq

# Expected: 201 Created with question object including:
# - id (integer)
# - text (your question)
# - upvote_count: 0
# - created_at (ISO timestamp)
```

## Validation Scenario 2: Host Question Visibility

### Test Case 2.1: View Questions on Host Dashboard

**Steps**:
1. Open http://localhost:3000/host/dashboard
2. Enter host code (e.g., `host_mvvk6e8n8luz`) and click "Access Dashboard"
3. Navigate to "Questions" tab

**Expected Result**:
- ✅ All submitted questions appear in the list
- ✅ Questions ordered by upvotes (DESC), then creation time (ASC)
- ✅ Each question shows:
  - Question text
  - Upvote count
  - Author name (or "Anonymous")
  - Created timestamp
  - "Mark as Answered" button
  - "Delete" button

### Test Case 2.2: Real-Time Updates (WebSocket)

**Steps**:
1. Keep host dashboard open
2. In another browser/tab, submit a question as attendee
3. Return to host dashboard

**Expected Result**:
- ✅ New question appears immediately (within 2 seconds) without page refresh
- ✅ Question displays with highlight animation
- ✅ Questions automatically re-sort if upvote count changes

### Test Case 2.3: Verify SQL Fix (Vote Ordering)

```bash
# Create questions with different vote counts
EVENT_ID=$(sqlite3 slido_clone.db "SELECT id FROM events WHERE short_code='ABC123';")

# Question 1 (will have 5 votes)
Q1_ID=$(curl -X POST http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Content-Type: application/json" \
  -H "Authorization: Attendee attendee_q1" \
  -d '{"text": "Question with 5 upvotes"}' | jq -r '.id')

# Question 2 (will have 10 votes)
Q2_ID=$(curl -X POST http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Content-Type: application/json" \
  -H "Authorization: Attendee attendee_q2" \
  -d '{"text": "Question with 10 upvotes"}' | jq -r '.id')

# Add upvotes
for i in {1..5}; do
  curl -X POST http://localhost:8001/api/v1/questions/$Q1_ID/upvote \
    -H "Authorization: Attendee voter_$i"
done

for i in {1..10}; do
  curl -X POST http://localhost:8001/api/v1/questions/$Q2_ID/upvote \
    -H "Authorization: Attendee voter_$(($i + 20))"
done

# Fetch questions via API (should be ordered by votes DESC)
curl -X GET http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Authorization: Host host_mvvk6e8n8luz" | jq '.[] | {id, text, upvote_count}'

# Expected order:
# 1. Question with 10 upvotes (upvote_count: 10)
# 2. Question with 5 upvotes (upvote_count: 5)
# 3. Other questions (upvote_count: 0, ordered by created_at ASC)
```

### Test Case 2.4: Performance Validation

```bash
# Create 1000 questions
EVENT_ID=$(sqlite3 slido_clone.db "SELECT id FROM events WHERE short_code='ABC123';")

for i in {1..1000}; do
  curl -X POST http://localhost:8001/api/v1/events/$EVENT_ID/questions \
    -H "Content-Type: application/json" \
    -H "Authorization: Attendee attendee_perf_$i" \
    -d "{\"text\": \"Performance test question $i\"}" > /dev/null 2>&1
done

# Measure GET questions latency
time curl -X GET http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Authorization: Host host_mvvk6e8n8luz" > /dev/null

# Expected: <200ms (per data-model.md p95 target)
```

## Validation Scenario 3: Custom Host Code

### Test Case 3.1: Create Event with Custom Host Code via UI

**Steps**:
1. Open http://localhost:3000/create-event
2. Enter event details:
   - Title: "Team All-Hands Q&A"
   - Description: "Monthly team meeting Q&A session"
3. Toggle "Use custom host code"
4. Enter custom host code: "host_myteam12345"
5. Click "Create Event"

**Expected Result**:
- ✅ Event created successfully
- ✅ Redirect to event page with short code (e.g., ABC456)
- ✅ Success message shows custom host code: "Event created! Your host code is: host_myteam12345"

### Test Case 3.2: Custom Host Code Validation

**Test Invalid Format**:
1. Enter custom host code: "mycode123" (missing "host_" prefix)
2. Click "Create Event"
3. **Expected**: Error "Host code must start with 'host_' and contain only lowercase letters and numbers (e.g., host_abc123def456)"

**Test Duplicate Host Code**:
1. Try to create another event with "host_myteam12345"
2. **Expected**: Error "Host code already in use. Please choose a different code."

### Test Case 3.3: Direct API Testing

```bash
# Create event with custom host code
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Launch Event",
    "description": "Q&A for new product launch",
    "host_code": "host_launch2025"
  }' | jq

# Expected: 201 Created with:
# - id, title, short_code
# - host_code: "host_launch2025"

# Verify uniqueness constraint
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Another Event",
    "host_code": "host_launch2025"
  }'

# Expected: 409 Conflict with error message about duplicate
```

### Test Case 3.4: Auto-Generated Host Code (Default)

```bash
# Create event WITHOUT custom host code
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Auto-Generated Code Event"
  }' | jq -r '.host_code'

# Expected: Auto-generated code like "host_a8b9c0d1e2f3"
# Verify format: starts with "host_", followed by 12 alphanumeric chars
```

## Validation Scenario 4: Host Code Display

### Test Case 4.1: View Host Code on Dashboard

**Steps**:
1. Open http://localhost:3000/host/dashboard
2. Enter host code: "host_myteam12345"
3. Click "Access Dashboard"

**Expected Result**:
- ✅ Host code displayed prominently at top of dashboard
- ✅ Format: "Host Code: host_myteam12345" with copy icon
- ✅ Clicking copy icon copies code to clipboard and shows "Copied!" tooltip
- ✅ Host code visible on all dashboard tabs (Questions, Polls, Settings)

### Test Case 4.2: Copy to Clipboard

**Steps**:
1. Click the copy icon next to host code
2. Open text editor and paste (Cmd+V / Ctrl+V)

**Expected Result**:
- ✅ Exact host code pasted: "host_myteam12345"
- ✅ Toast notification: "Host code copied to clipboard"

### Test Case 4.3: Host Code Persistence

**Steps**:
1. Access dashboard with host code
2. Refresh page (F5)
3. Check if host code still displayed

**Expected Result**:
- ✅ Host code persists in localStorage/session
- ✅ No need to re-enter host code after refresh

## Validation Scenario 5: Multi-Event Creation

### Test Case 5.1: Create Multiple Events

**Steps**:
1. Create first event:
   - Title: "Event 1: Team Meeting"
   - Custom code: "host_event1_2025"
2. Click "Create Another Event" button on success page
3. Create second event:
   - Title: "Event 2: Product Demo"
   - Custom code: "host_event2_2025"
4. Repeat for third event:
   - Title: "Event 3: Training Session"
   - Custom code: "host_event3_2025"

**Expected Result**:
- ✅ All 3 events created with different host codes
- ✅ Each has unique short code (e.g., ABC123, DEF456, GHI789)

### Test Case 5.2: Event Switcher Dropdown

**Steps**:
1. Access dashboard with "host_event1_2025"
2. Click "Event Switcher" dropdown in top navigation

**Expected Result**:
- ✅ Dropdown shows all 3 events created by this host:
  - Event 1: Team Meeting (ABC123) - 5 questions
  - Event 2: Product Demo (DEF456) - 2 questions
  - Event 3: Training Session (GHI789) - 0 questions
- ✅ Currently selected event highlighted
- ✅ Each entry shows: title, short code, question count

**Steps (continued)**:
3. Select "Event 2: Product Demo" from dropdown

**Expected Result**:
- ✅ Dashboard updates to show Event 2's questions
- ✅ URL updates to include Event 2's ID/code
- ✅ No page refresh (smooth transition)

### Test Case 5.3: Pagination (20+ Events)

```bash
# Create 45 events with same host code
for i in {1..45}; do
  curl -X POST http://localhost:8001/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{
      \"title\": \"Event $i\",
      \"host_code\": \"host_multitest\"
    }" > /dev/null 2>&1
done

# Fetch first page (20 events)
curl -X GET "http://localhost:8001/api/v1/events/host?page=1&per_page=20" \
  -H "Authorization: Host host_multitest" | jq '{total, page, per_page, total_pages, event_count: (.events | length)}'

# Expected:
# {
#   "total": 45,
#   "page": 1,
#   "per_page": 20,
#   "total_pages": 3,
#   "event_count": 20
# }

# Fetch last page (5 events)
curl -X GET "http://localhost:8001/api/v1/events/host?page=3&per_page=20" \
  -H "Authorization: Host host_multitest" | jq '.events | length'

# Expected: 5
```

### Test Case 5.4: Event Switcher UI with Pagination

**Steps**:
1. Access dashboard with "host_multitest" (45 events)
2. Click Event Switcher dropdown

**Expected Result**:
- ✅ Shows first 20 events
- ✅ "Load More" button at bottom of dropdown
- ✅ Page indicator: "Showing 1-20 of 45"

**Steps (continued)**:
3. Click "Load More"

**Expected Result**:
- ✅ Shows next 20 events (21-40)
- ✅ Previous events still visible (infinite scroll style)
- ✅ Page indicator: "Showing 1-40 of 45"

4. Click "Load More" again

**Expected Result**:
- ✅ Shows final 5 events (41-45)
- ✅ "Load More" button disappears
- ✅ Page indicator: "Showing 1-45 of 45"

### Test Case 5.5: Event Isolation (Host Cannot See Other Hosts' Events)

```bash
# Create events with different host codes
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"title": "Host A Event 1", "host_code": "host_hosta12345"}'

curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"title": "Host A Event 2", "host_code": "host_hosta12345"}'

curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"title": "Host B Event 1", "host_code": "host_hostb67890"}'

# Host A fetches events
curl -X GET "http://localhost:8001/api/v1/events/host" \
  -H "Authorization: Host host_hosta12345" | jq '.events | length'

# Expected: 2 (only Host A's events)

# Host B fetches events
curl -X GET "http://localhost:8001/api/v1/events/host" \
  -H "Authorization: Host host_hostb67890" | jq '.events | length'

# Expected: 1 (only Host B's event)
```

## Integration Test: Complete User Flow

### Flow 1: Host Creates Event → Attendee Submits Question → Host Views Question

```bash
# Step 1: Host creates event
EVENT=$(curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Integration Test Event",
    "description": "End-to-end test",
    "host_code": "host_integration"
  }')

EVENT_ID=$(echo $EVENT | jq -r '.id')
SHORT_CODE=$(echo $EVENT | jq -r '.short_code')
HOST_CODE=$(echo $EVENT | jq -r '.host_code')

echo "Event created: ID=$EVENT_ID, Short Code=$SHORT_CODE, Host Code=$HOST_CODE"

# Step 2: Attendee submits question
QUESTION=$(curl -X POST http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Content-Type: application/json" \
  -H "Authorization: Attendee attendee_alice" \
  -d '{
    "text": "What are the key features of this product?",
    "is_anonymous": false
  }')

QUESTION_ID=$(echo $QUESTION | jq -r '.id')
echo "Question submitted: ID=$QUESTION_ID"

# Step 3: Another attendee upvotes
curl -X POST http://localhost:8001/api/v1/questions/$QUESTION_ID/upvote \
  -H "Authorization: Attendee attendee_bob"

echo "Question upvoted by attendee_bob"

# Step 4: Host fetches questions
QUESTIONS=$(curl -X GET http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Authorization: Host $HOST_CODE")

echo "Host views questions:"
echo $QUESTIONS | jq '.[] | {id, text, upvote_count}'

# Expected:
# {
#   "id": <QUESTION_ID>,
#   "text": "What are the key features of this product?",
#   "upvote_count": 1
# }
```

### Flow 2: WebSocket Real-Time Updates

**Terminal 1 (WebSocket listener)**:
```bash
# Install websocat if not already: brew install websocat
EVENT_ID=<your_event_id>
websocat "ws://localhost:8001/api/v1/ws/events/$EVENT_ID?token=host_integration"
```

**Terminal 2 (Submit question)**:
```bash
EVENT_ID=<your_event_id>
curl -X POST http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Content-Type: application/json" \
  -H "Authorization: Attendee attendee_charlie" \
  -d '{"text": "WebSocket test question"}'
```

**Expected in Terminal 1**:
```json
{
  "type": "question_created",
  "event_id": <EVENT_ID>,
  "question": {
    "id": <QUESTION_ID>,
    "text": "WebSocket test question",
    "upvote_count": 0,
    ...
  },
  "timestamp": "2025-10-08T..."
}
```

## Performance Benchmarks

### Benchmark 1: Question Submission Latency (<500ms)
```bash
EVENT_ID=<your_event_id>

# Run 10 submissions and measure average latency
for i in {1..10}; do
  time curl -X POST http://localhost:8001/api/v1/events/$EVENT_ID/questions \
    -H "Content-Type: application/json" \
    -H "Authorization: Attendee attendee_bench_$i" \
    -d "{\"text\": \"Benchmark question $i\"}" > /dev/null 2>&1
done

# Expected: All responses <500ms (per NFR-001)
```

### Benchmark 2: Question Retrieval with Ordering (<200ms)
```bash
EVENT_ID=<your_event_id>

# Measure GET /questions latency with 1000 questions
time curl -X GET http://localhost:8001/api/v1/events/$EVENT_ID/questions \
  -H "Authorization: Host host_integration" > /dev/null

# Expected: <200ms p95 (per data-model.md)
```

### Benchmark 3: WebSocket Broadcast Latency (<2s)
Use the integration test above and measure timestamp difference:
```
Server sends "question_created" at timestamp T1
Client receives message at timestamp T2
Latency = T2 - T1
```
**Expected**: <2 seconds (per NFR-002)

## Troubleshooting

### Issue: Questions Not Appearing on Dashboard
**Check**:
1. Verify WebSocket connection: Browser DevTools → Network → WS tab → Check if connected
2. Check backend logs for errors: `tail -f backend/logs/app.log`
3. Test API directly: `curl -X GET http://localhost:8001/api/v1/events/$EVENT_ID/questions -H "Authorization: Host <host_code>"`

### Issue: "Host Code Already in Use" Error
**Check**:
```bash
# List all host codes in database
sqlite3 slido_clone.db "SELECT id, title, host_code FROM events;"

# Delete conflicting event if needed
sqlite3 slido_clone.db "DELETE FROM events WHERE host_code='<conflicting_code>';"
```

### Issue: Event Switcher Not Loading
**Check**:
1. Verify pagination API: `curl -X GET "http://localhost:8001/api/v1/events/host?page=1" -H "Authorization: Host <host_code>"`
2. Check browser console for JavaScript errors
3. Verify host code authentication: Ensure `Authorization` header is being sent

### Issue: Rate Limiting False Positives
**Check**:
1. Verify rate limit implementation uses attendee_id, not IP (multiple attendees from same network)
2. Reset rate limit: Restart backend server (rate limits stored in memory)

## Success Criteria Checklist

- [ ] **FR-001**: Attendees can submit questions (1-1000 chars) ✅
- [ ] **FR-002**: Host can see all questions ordered by votes DESC, created_at ASC ✅
- [ ] **FR-003**: Events can be created with custom host codes (format: `host_[a-z0-9]{12}`) ✅
- [ ] **FR-004**: Host code displayed on dashboard with copy functionality ✅
- [ ] **FR-005**: Hosts can create multiple events with different host codes ✅
- [ ] **FR-006**: Event switcher shows paginated list (20/page) of host's events ✅
- [ ] **FR-007**: WebSocket broadcasts question updates in <2s ✅
- [ ] **NFR-001**: Question submission <500ms ✅
- [ ] **NFR-002**: Real-time updates <2s ✅
- [ ] **NFR-003**: p95 database queries <200ms ✅
- [ ] **NFR-004**: 85% code coverage (run `pytest --cov`) ✅

## Next Steps

After validating all scenarios:
1. Run full test suite: `pytest tests/ --cov=src --cov-report=html`
2. Check coverage report: `open htmlcov/index.html`
3. Run frontend tests: `cd frontend && npm test`
4. Deploy to staging environment
5. Perform UAT with real users

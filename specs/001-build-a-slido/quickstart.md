# Quickstart Testing Guide: Live Q&A & Polls Application

**Purpose**: End-to-end validation scenarios for complete user workflows  
**Environment**: Local development with Docker Compose  
**Prerequisites**: All services running, database initialized

## Setup Instructions

### 1. Start Development Environment
```bash
# Clone and navigate to project
git clone <repository-url>
cd slido-clone

# Start all services
docker-compose up -d

# Verify services are running
curl http://localhost:8000/health  # Backend health check
curl http://localhost:3000         # Frontend accessible
```

### 2. Database Initialization
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Optional: Load test data
docker-compose exec backend python scripts/seed_test_data.py
```

---

## Test Scenario 1: Complete Host Workflow

### Host Creates Event
```bash
# Create new event
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "React Performance Workshop",
    "slug": "react-perf-2025",
    "description": "Learn optimization techniques"
  }'

# Expected response includes host_code and short_code
# Save host_code for subsequent requests
```

### Host Creates and Opens Poll
```bash
# Create poll (using host_code from previous step)
curl -X POST http://localhost:8000/api/v1/events/1/polls \
  -H "Content-Type: application/json" \
  -H "Authorization: Host <host_code>" \
  -d '{
    "question_text": "What React performance issue affects you most?",
    "poll_type": "single",
    "options": [
      {"option_text": "Unnecessary re-renders", "position": 0},
      {"option_text": "Large bundle sizes", "position": 1},
      {"option_text": "Memory leaks", "position": 2},
      {"option_text": "Slow initial load", "position": 3}
    ]
  }'

# Open poll for voting
curl -X PUT http://localhost:8000/api/v1/events/1/polls/1/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Host <host_code>" \
  -d '{"status": "open"}'
```

### Validation Checkpoints
- [ ] Event created with valid slug and codes
- [ ] Poll created in 'draft' status initially  
- [ ] Poll status successfully changed to 'open'
- [ ] Host dashboard shows created poll
- [ ] WebSocket connection established for real-time updates

---

## Test Scenario 2: Attendee Participation Flow

### Attendee Joins Event
```bash
# Join event using slug
curl -X POST http://localhost:8000/api/v1/events/react-perf-2025/join \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Sarah Chen",
    "is_anonymous": false
  }'

# Expected response includes session_id
# Save session_id for subsequent requests
```

### Attendee Views Available Polls
```bash
# Get active polls
curl http://localhost:8000/api/v1/events/1/polls?status=open \
  -H "X-Attendee-Session: <session_id>"

# Verify poll appears with options and zero votes
```

### Attendee Votes on Poll
```bash
# Submit vote for option 1 (Unnecessary re-renders)
curl -X POST http://localhost:8000/api/v1/events/1/polls/1/vote \
  -H "Content-Type: application/json" \
  -H "X-Attendee-Session: <session_id>" \
  -d '{"option_ids": [1]}'

# Verify vote recorded successfully
```

### Validation Checkpoints  
- [ ] Attendee successfully joins with display name
- [ ] Available polls visible to attendee
- [ ] Vote submission returns success
- [ ] Poll results update in real-time via WebSocket
- [ ] Vote count and percentage calculations correct

---

## Test Scenario 3: Q&A Moderation Workflow

### Attendee Submits Question
```bash
# Submit question to queue
curl -X POST http://localhost:8000/api/v1/events/1/questions \
  -H "Content-Type: application/json" \
  -H "X-Attendee-Session: <session_id>" \
  -d '{
    "question_text": "What are the best practices for React.memo usage?"
  }'

# Expected: Question created with 'pending' status
```

### Host Reviews and Approves Question
```bash
# Get pending questions (host view)
curl http://localhost:8000/api/v1/events/1/questions?status=pending \
  -H "Authorization: Host <host_code>"

# Approve the question
curl -X PUT http://localhost:8000/api/v1/events/1/questions/1/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Host <host_code>" \
  -d '{"status": "approved"}'
```

### Other Attendees Upvote Question
```bash
# Simulate second attendee joining
curl -X POST http://localhost:8000/api/v1/events/react-perf-2025/join \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Mike Rodriguez", 
    "is_anonymous": false
  }'

# Second attendee upvotes the question
curl -X POST http://localhost:8000/api/v1/events/1/questions/1/upvote \
  -H "X-Attendee-Session: <second_session_id>"

# Verify upvote count increases and queue reorders
```

### Validation Checkpoints
- [ ] Question submitted and appears in host's pending queue
- [ ] Question approval makes it visible to all attendees
- [ ] Upvote functionality works and updates counts in real-time
- [ ] Question queue reorders by upvote count
- [ ] WebSocket events broadcast question status changes

---

## Test Scenario 4: Real-time Synchronization

### Multi-Attendee Poll Voting
```bash
# Simulate 5 attendees joining and voting simultaneously
for i in {1..5}; do
  # Join as attendee
  session=$(curl -s -X POST http://localhost:8000/api/v1/events/react-perf-2025/join \
    -H "Content-Type: application/json" \
    -d "{\"display_name\": \"Attendee $i\", \"is_anonymous\": false}" \
    | jq -r '.session_id')
  
  # Vote on random option
  option=$((1 + RANDOM % 4))
  curl -X POST http://localhost:8000/api/v1/events/1/polls/1/vote \
    -H "Content-Type: application/json" \
    -H "X-Attendee-Session: $session" \
    -d "{\"option_ids\": [$option]}" &
done

wait  # Wait for all votes to complete
```

### WebSocket Real-time Testing
```javascript
// Frontend JavaScript to test WebSocket updates
const ws = new WebSocket('ws://localhost:8000/ws/react-perf-2025?session_id=test_session');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log(`Received: ${data.event_type}`, data);
  
  // Verify message delivery time < 100ms
  if (data.timestamp) {
    const latency = Date.now() - new Date(data.timestamp).getTime();
    console.log(`Latency: ${latency}ms`);
  }
};
```

### Validation Checkpoints
- [ ] Multiple simultaneous votes processed correctly
- [ ] Real-time updates delivered within 100ms
- [ ] Vote counts remain consistent across all clients
- [ ] No race conditions in vote tallying
- [ ] WebSocket connections stable under load

---

## Test Scenario 5: Error Handling and Edge Cases

### Invalid Requests
```bash
# Try to vote on closed poll
curl -X PUT http://localhost:8000/api/v1/events/1/polls/1/status \
  -H "Authorization: Host <host_code>" \
  -d '{"status": "closed"}'

curl -X POST http://localhost:8000/api/v1/events/1/polls/1/vote \
  -H "X-Attendee-Session: <session_id>" \
  -d '{"option_ids": [1]}'
# Expected: 400 Bad Request - Poll not open

# Try to vote twice
curl -X PUT http://localhost:8000/api/v1/events/1/polls/1/status \
  -H "Authorization: Host <host_code>" \
  -d '{"status": "open"}'

curl -X POST http://localhost:8000/api/v1/events/1/polls/1/vote \
  -H "X-Attendee-Session: <session_id>" \
  -d '{"option_ids": [2]}'
# Expected: 409 Conflict - Already voted
```

### Session Recovery
```bash
# Simulate connection drop and reconnect
# Close WebSocket connection, then reconnect with same session_id
# Verify state sync occurs within 5 seconds
```

### Validation Checkpoints
- [ ] Appropriate error codes returned for invalid operations
- [ ] Duplicate vote prevention works correctly
- [ ] Connection recovery restores proper state
- [ ] Error messages are clear and actionable
- [ ] System degrades gracefully under failure conditions

---

## Performance Validation

### Load Testing
```bash
# Use artillery.js for load testing
npm install -g artillery

# Test WebSocket connections
artillery run websocket-load-test.yml

# Test HTTP API throughput  
artillery run api-load-test.yml
```

### Expected Performance Metrics
- [ ] API response times < 300ms for 95th percentile
- [ ] WebSocket message delivery < 100ms
- [ ] System stable with 100 concurrent attendees
- [ ] Memory usage remains under 512MB per 100 users
- [ ] CPU usage stays below 80% under normal load

---

## Cleanup
```bash
# Stop all services
docker-compose down

# Remove test data (optional)
docker-compose exec backend python scripts/cleanup_test_data.py

# Reset database (if needed)
docker-compose down -v  # Removes volumes including database
```

---

## Success Criteria Summary

**Functional Requirements**: ✅ All CRUD operations work correctly  
**Real-time Features**: ✅ WebSocket updates delivered within 100ms  
**Data Persistence**: ✅ All votes and questions persist across restarts  
**Authentication**: ✅ Host codes protect management functions  
**User Experience**: ✅ Attendees can participate anonymously or with names  
**Error Handling**: ✅ Graceful degradation and clear error messages  
**Performance**: ✅ Meets constitutional performance requirements  

**Constitution Compliance**: ✅ Test-first approach validated, performance benchmarks met, accessibility standards followed
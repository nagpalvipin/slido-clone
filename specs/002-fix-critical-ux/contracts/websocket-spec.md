# WebSocket Contract: Real-Time Event Updates

## Connection

### Endpoint
```
ws://localhost:8001/api/v1/ws/events/{event_id}
```

### Authentication
```
?token={attendee_id_or_host_code}
```

### Example Connection
```javascript
// Attendee connection
const ws = new WebSocket('ws://localhost:8001/api/v1/ws/events/42?token=attendee_alice123');

// Host connection
const ws = new WebSocket('ws://localhost:8001/api/v1/ws/events/42?token=host_mvvk6e8n8luz');
```

## Connection Lifecycle

### 1. Connection Established
**Client receives**:
```json
{
  "type": "connection_established",
  "event_id": 42,
  "client_id": "conn_abc123def456",
  "role": "attendee | host",
  "timestamp": "2025-10-08T15:45:22Z"
}
```

### 2. Heartbeat (Every 30s)
**Server sends**:
```json
{
  "type": "ping",
  "timestamp": "2025-10-08T15:45:52Z"
}
```

**Client responds**:
```json
{
  "type": "pong",
  "timestamp": "2025-10-08T15:45:52Z"
}
```

### 3. Connection Closed
**Server sends** (before closing):
```json
{
  "type": "connection_closing",
  "reason": "Server shutdown | Timeout | Invalid token",
  "timestamp": "2025-10-08T16:00:00Z"
}
```

## Message Types

### question_created
**When**: New question submitted to event (POST /events/{event_id}/questions → 201)

**Broadcast to**: All clients connected to this event

**Payload**:
```json
{
  "type": "question_created",
  "event_id": 42,
  "question": {
    "id": 1001,
    "event_id": 42,
    "text": "What is the expected timeline for the new feature rollout?",
    "is_anonymous": false,
    "author_name": "Alice Johnson",
    "upvote_count": 0,
    "created_at": "2025-10-08T15:45:22Z",
    "is_answered": false,
    "user_has_upvoted": false
  },
  "timestamp": "2025-10-08T15:45:22Z"
}
```

**Frontend Behavior**:
- Add question to questions list
- Display with highlight animation (FR-004 clarification)
- Sort by upvote_count DESC, created_at ASC
- Auto-scroll if user is near bottom of list

### question_upvoted
**When**: Attendee upvotes a question (POST /questions/{question_id}/upvote → 200)

**Broadcast to**: All clients connected to this event

**Payload**:
```json
{
  "type": "question_upvoted",
  "event_id": 42,
  "question_id": 1001,
  "upvote_count": 15,
  "upvoter_id": "attendee_bob456",
  "timestamp": "2025-10-08T15:46:10Z"
}
```

**Frontend Behavior**:
- Update upvote count for question with ID 1001
- Re-sort questions list (may change position)
- Animate count change (e.g., "+1" effect)
- If current user upvoted, update button state to "upvoted"

### question_unupvoted
**When**: Attendee removes upvote (DELETE /questions/{question_id}/upvote → 200)

**Broadcast to**: All clients connected to this event

**Payload**:
```json
{
  "type": "question_unupvoted",
  "event_id": 42,
  "question_id": 1001,
  "upvote_count": 14,
  "unupvoter_id": "attendee_bob456",
  "timestamp": "2025-10-08T15:46:30Z"
}
```

**Frontend Behavior**:
- Update upvote count for question with ID 1001
- Re-sort questions list
- If current user unupvoted, update button state to "not upvoted"

### question_answered
**When**: Host marks question as answered (PATCH /questions/{question_id} → 200)

**Broadcast to**: All clients connected to this event

**Payload**:
```json
{
  "type": "question_answered",
  "event_id": 42,
  "question_id": 1001,
  "is_answered": true,
  "answered_at": "2025-10-08T15:50:00Z",
  "timestamp": "2025-10-08T15:50:00Z"
}
```

**Frontend Behavior**:
- Update question `is_answered` status
- Apply visual indicator (e.g., checkmark, different background)
- Optionally move to "Answered" section if UI has separate sections

### question_deleted
**When**: Host deletes question (DELETE /questions/{question_id} → 204)

**Broadcast to**: All clients connected to this event

**Payload**:
```json
{
  "type": "question_deleted",
  "event_id": 42,
  "question_id": 1001,
  "timestamp": "2025-10-08T15:55:00Z"
}
```

**Frontend Behavior**:
- Remove question from list with fade-out animation
- Update question count display

### event_updated
**When**: Host updates event details (PATCH /events/{event_id} → 200)

**Broadcast to**: All clients connected to this event

**Payload**:
```json
{
  "type": "event_updated",
  "event_id": 42,
  "updates": {
    "title": "Updated Team All-Hands Q&A",
    "is_active": false
  },
  "timestamp": "2025-10-08T16:00:00Z"
}
```

**Frontend Behavior**:
- Update event title if changed
- If `is_active: false`, show "Event has ended" message
- Disable question submission if inactive

### error
**When**: Invalid message format or unauthorized action

**Sent to**: Individual client who sent invalid message

**Payload**:
```json
{
  "type": "error",
  "code": "INVALID_MESSAGE | UNAUTHORIZED | RATE_LIMIT_EXCEEDED",
  "message": "Human-readable error description",
  "timestamp": "2025-10-08T15:45:22Z"
}
```

**Examples**:
```json
// Invalid JSON
{
  "type": "error",
  "code": "INVALID_MESSAGE",
  "message": "Invalid JSON format",
  "timestamp": "2025-10-08T15:45:22Z"
}

// Attendee tries to delete question
{
  "type": "error",
  "code": "UNAUTHORIZED",
  "message": "Only hosts can delete questions",
  "timestamp": "2025-10-08T15:45:22Z"
}
```

## Client → Server Messages

### upvote_question
**Purpose**: Request to upvote a question

**Payload**:
```json
{
  "type": "upvote_question",
  "question_id": 1001
}
```

**Response**: `question_upvoted` broadcast OR `error` message

### unupvote_question
**Purpose**: Request to remove upvote

**Payload**:
```json
{
  "type": "unupvote_question",
  "question_id": 1001
}
```

**Response**: `question_unupvoted` broadcast OR `error` message

### mark_answered (Host Only)
**Purpose**: Mark question as answered

**Payload**:
```json
{
  "type": "mark_answered",
  "question_id": 1001,
  "is_answered": true
}
```

**Response**: `question_answered` broadcast OR `error` message

### delete_question (Host Only)
**Purpose**: Delete a question

**Payload**:
```json
{
  "type": "delete_question",
  "question_id": 1001
}
```

**Response**: `question_deleted` broadcast OR `error` message

## Performance Requirements

### Latency (NFR-002)
- Target: <2 seconds from action to all clients receiving update
- Measured: Server event timestamp → client received timestamp
- 95th percentile must be <2s even with 100 concurrent connections

### Connection Limits
- Max connections per event: 1000 clients
- If exceeded, return 503 Service Unavailable on new connections

### Message Rate Limits
- Attendee: 10 messages/minute (excluding pong)
- Host: 100 messages/minute
- If exceeded, send `error` with `RATE_LIMIT_EXCEEDED` and close connection after 3 violations

### Reconnection Policy
- Client should reconnect with exponential backoff on disconnect
- Backoff: 1s, 2s, 4s, 8s, 16s (max)
- After reconnect, client should fetch latest question list via HTTP API

## Error Handling

### Connection Errors
| Code | Reason | Client Action |
|------|--------|---------------|
| 1000 | Normal closure | No reconnection needed |
| 1001 | Going away (server shutdown) | Reconnect after 5s |
| 1002 | Protocol error | Show error, no reconnection |
| 1003 | Invalid data | Show error, no reconnection |
| 1008 | Policy violation (rate limit) | Wait 60s, then reconnect |
| 1011 | Internal server error | Reconnect with backoff |

### Message Validation
All incoming messages must:
- Be valid JSON
- Have `type` field (string)
- Have required fields for that message type
- Pass authorization check (e.g., only host can delete)

Invalid messages trigger `error` response and count toward rate limit.

## Test Scenarios

### Contract Test: Connection Established
```python
async def test_websocket_connection_established():
    async with client.websocket_connect(
        f"/api/v1/ws/events/42?token=attendee_test123"
    ) as ws:
        message = await ws.receive_json()
        assert message["type"] == "connection_established"
        assert message["event_id"] == 42
        assert message["role"] == "attendee"
```

### Contract Test: Question Created Broadcast
```python
async def test_question_created_broadcast():
    event = create_event("Test", "test", "host_test123")
    
    # Connect two clients
    async with client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=attendee_alice"
    ) as ws1, client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=attendee_bob"
    ) as ws2:
        # Clear connection messages
        await ws1.receive_json()
        await ws2.receive_json()
        
        # Submit question via HTTP
        response = client.post(
            f"/api/v1/events/{event.id}/questions",
            json={"text": "Test question"},
            headers={"Authorization": "Attendee attendee_alice"}
        )
        assert response.status_code == 201
        
        # Both clients should receive broadcast
        msg1 = await ws1.receive_json()
        msg2 = await ws2.receive_json()
        
        assert msg1["type"] == "question_created"
        assert msg1["question"]["text"] == "Test question"
        assert msg2 == msg1  # Identical message
```

### Contract Test: Upvote Broadcast
```python
async def test_upvote_question_broadcast():
    event = create_event("Test", "test", "host_test123")
    question = create_question(event.id, "Test question")
    
    async with client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=attendee_alice"
    ) as ws:
        await ws.receive_json()  # Clear connection message
        
        # Send upvote message
        await ws.send_json({
            "type": "upvote_question",
            "question_id": question.id
        })
        
        # Receive broadcast
        msg = await ws.receive_json()
        assert msg["type"] == "question_upvoted"
        assert msg["question_id"] == question.id
        assert msg["upvote_count"] == 1
```

### Contract Test: Host-Only Action (Delete)
```python
async def test_delete_question_host_only():
    event = create_event("Test", "test", "host_test123")
    question = create_question(event.id, "Test")
    
    # Attendee tries to delete
    async with client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=attendee_alice"
    ) as ws:
        await ws.receive_json()
        
        await ws.send_json({
            "type": "delete_question",
            "question_id": question.id
        })
        
        msg = await ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "UNAUTHORIZED"
    
    # Host can delete
    async with client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=host_test123"
    ) as ws:
        await ws.receive_json()
        
        await ws.send_json({
            "type": "delete_question",
            "question_id": question.id
        })
        
        msg = await ws.receive_json()
        assert msg["type"] == "question_deleted"
```

### Contract Test: Rate Limiting
```python
async def test_websocket_rate_limit():
    event = create_event("Test", "test", "host_test123")
    
    async with client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=attendee_alice"
    ) as ws:
        await ws.receive_json()
        
        # Send 11 messages rapidly (limit is 10/min)
        for i in range(11):
            await ws.send_json({
                "type": "upvote_question",
                "question_id": i
            })
        
        # Should receive error for 11th message
        messages = []
        for _ in range(11):
            messages.append(await ws.receive_json())
        
        error_msgs = [m for m in messages if m["type"] == "error"]
        assert len(error_msgs) > 0
        assert any(m["code"] == "RATE_LIMIT_EXCEEDED" for m in error_msgs)
```

### Contract Test: Heartbeat/Ping-Pong
```python
async def test_websocket_heartbeat():
    event = create_event("Test", "test", "host_test123")
    
    async with client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=attendee_alice"
    ) as ws:
        await ws.receive_json()  # connection_established
        
        # Wait for ping
        msg = await asyncio.wait_for(ws.receive_json(), timeout=35)
        assert msg["type"] == "ping"
        
        # Respond with pong
        await ws.send_json({"type": "pong"})
        
        # Connection should stay alive
        await asyncio.sleep(1)
        assert ws.client_state == WebSocketState.CONNECTED
```

### Contract Test: Invalid Message Format
```python
async def test_websocket_invalid_message():
    event = create_event("Test", "test", "host_test123")
    
    async with client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=attendee_alice"
    ) as ws:
        await ws.receive_json()
        
        # Send invalid JSON
        await ws.send_text("not valid json")
        
        msg = await ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "INVALID_MESSAGE"
```

### Performance Test: Latency <2s
```python
async def test_websocket_latency():
    event = create_event("Test", "test", "host_test123")
    
    async with client.websocket_connect(
        f"/api/v1/ws/events/{event.id}?token=attendee_alice"
    ) as ws:
        await ws.receive_json()
        
        # Submit question and measure broadcast latency
        start = time.time()
        response = client.post(
            f"/api/v1/events/{event.id}/questions",
            json={"text": "Latency test"},
            headers={"Authorization": "Attendee attendee_bob"}
        )
        
        msg = await ws.receive_json()
        latency = time.time() - start
        
        assert msg["type"] == "question_created"
        assert latency < 2.0  # <2s target per NFR-002
```

### Performance Test: 100 Concurrent Connections
```python
async def test_websocket_concurrent_connections():
    event = create_event("Test", "test", "host_test123")
    
    connections = []
    for i in range(100):
        ws = await client.websocket_connect(
            f"/api/v1/ws/events/{event.id}?token=attendee_{i}"
        )
        await ws.receive_json()  # Clear connection message
        connections.append(ws)
    
    # Broadcast a question
    start = time.time()
    response = client.post(
        f"/api/v1/events/{event.id}/questions",
        json={"text": "Broadcast to 100 clients"},
        headers={"Authorization": "Attendee attendee_test"}
    )
    
    # All clients should receive within 2s
    for ws in connections:
        msg = await asyncio.wait_for(ws.receive_json(), timeout=2.0)
        assert msg["type"] == "question_created"
    
    total_time = time.time() - start
    assert total_time < 2.0  # All 100 clients updated in <2s
```

## Frontend Integration

### WebSocket Hook Usage
```typescript
function useEventWebSocket(eventId: number, token: string) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);

  useEffect(() => {
    const socket = new WebSocket(
      `ws://localhost:8001/api/v1/ws/events/${eventId}?token=${token}`
    );

    socket.onopen = () => console.log('WebSocket connected');

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'question_created':
          setQuestions(prev => [...prev, message.question].sort(sortByVotes));
          highlightQuestion(message.question.id);
          break;

        case 'question_upvoted':
          setQuestions(prev =>
            prev.map(q =>
              q.id === message.question_id
                ? { ...q, upvote_count: message.upvote_count }
                : q
            ).sort(sortByVotes)
          );
          break;

        case 'question_deleted':
          setQuestions(prev => prev.filter(q => q.id !== message.question_id));
          break;

        case 'ping':
          socket.send(JSON.stringify({ type: 'pong' }));
          break;

        case 'error':
          console.error('WebSocket error:', message);
          break;
      }
    };

    socket.onclose = (event) => {
      console.log('WebSocket closed:', event.code);
      // Reconnect with backoff
      setTimeout(() => setWs(null), getBackoffDelay(event.code));
    };

    setWs(socket);

    return () => socket.close();
  }, [eventId, token]);

  return { ws, questions };
}
```

## Implementation Checklist
- [ ] Implement WebSocket endpoint `/api/v1/ws/events/{event_id}`
- [ ] Add token-based authentication
- [ ] Implement message routing/broadcasting
- [ ] Add heartbeat ping/pong mechanism
- [ ] Implement rate limiting per connection
- [ ] Add all message type handlers (created, upvoted, deleted, etc.)
- [ ] Implement host-only action authorization
- [ ] Write contract tests (all scenarios above)
- [ ] Add performance tests (latency <2s, 100 connections)
- [ ] Update frontend useEventWebSocket hook
- [ ] Add reconnection logic with exponential backoff

# Question Loading & API Fixes

## Issues Fixed

### 1. **Doubled API Path Bug** ❌ → ✅
**Problem**: Questions endpoint had doubled `/api/v1/` in URL
- Wrong: `/api/v1/api/v1/events/97/questions` 
- Logs showed: `404 Not Found`

**Root Cause**: In `frontend/src/services/api.ts` line 324, the fallback used `/api/v1/events/...` but `baseUrl` already includes `/api/v1`

**Fix**: Changed to relative path
```typescript
// Before (WRONG)
return await apiClient.get<Question[]>(`/api/v1/events/${event.id}/questions`);

// After (FIXED)
return await apiClient.get<Question[]>(`/events/${event.id}/questions`);
```

### 2. **Missing EventSwitcher Endpoint** ❌ → ✅
**Problem**: EventSwitcher component calling non-existent endpoint
- URL: `GET /api/v1/events/host/host_buu7w0kf3fac?limit=20`
- Logs showed: `404 Not Found`

**Fix**: Added new endpoint to backend

**File**: `backend/src/services/event_service.py`
```python
def get_events_by_host_code(
    self, 
    host_code: str, 
    limit: int = 20, 
    offset: int = 0
) -> tuple[List[Event], int]:
    """Get events for a specific host_code with pagination."""
    query = self.db.query(Event).filter(Event.host_code == host_code)
    total = query.count()
    events = query.order_by(Event.created_at.desc()).limit(limit).offset(offset).all()
    return events, total
```

**File**: `backend/src/api/events.py`
```python
@router.get("/host/{host_code}", response_model=Dict[str, Any])
async def get_events_by_host(
    host_code: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all events for a specific host code with pagination."""
    service = EventService(db)
    events, total = service.get_events_by_host_code(host_code, limit, offset)
    
    # Format and return events with question_count
    ...
```

### 3. **401 Unauthorized Issues** 🔍
**Observed**: Multiple `401 Unauthorized` errors for `/api/v1/events/vipin/host`

**Cause**: Frontend not sending `Authorization: Host <code>` header correctly, or using wrong/stale host_code

**Note**: This needs frontend localStorage/auth debugging. The backend expects:
```
Authorization: Host host_xxxxx
```

### 4. **WebSocket 403 Errors** 🔍
**Observed**: `WebSocket /ws/events/event 403 Forbidden`

**Cause**: Frontend trying to connect to `/ws/events/event` (invalid slug)
- Should be: `/ws/events/{actual-event-slug}`
- Example working: `/ws/events/vipin` [accepted]

**Action**: Check frontend WebSocket connection code - it's using hardcoded "event" slug

## Files Modified

### Frontend
1. ✅ `frontend/src/services/api.ts` - Fixed doubled API path in questions fallback

### Backend  
2. ✅ `backend/src/services/event_service.py` - Added `get_events_by_host_code()` method
3. ✅ `backend/src/api/events.py` - Added `GET /host/{host_code}` endpoint

## Testing

### Test Question Creation & Display
```bash
# 1. Create event
curl -X POST http://localhost:8001/api/v1/events/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Q&A","slug":"test-qa","host_code":"testhost"}'

# 2. Create question
curl -X POST http://localhost:8001/api/v1/events/8/questions \
  -H "Content-Type: application/json" \
  -d '{"question_text":"How does this work?"}'

# 3. Get questions (FIXED - no more 404!)
curl http://localhost:8001/api/v1/events/8/questions

# 4. Test EventSwitcher endpoint (NEW!)
curl http://localhost:8001/api/v1/events/host/host_testhost?limit=20
```

### Expected Results
1. ✅ Questions endpoint returns `200 OK` (not 404)
2. ✅ EventSwitcher loads host's events
3. ✅ Frontend displays questions in real-time

## Remaining Issues to Debug

### Issue 1: Authorization Header
**Symptom**: `401 Unauthorized` on host dashboard
**Check**: 
- Is `hostCode` being stored in localStorage?
- Is `Authorization` header being sent?
- Debug in browser DevTools → Network → Request Headers

### Issue 2: WebSocket Connection
**Symptom**: `/ws/events/event` 403 Forbidden
**Check**:
- Frontend WebSocket code - find where it connects
- Should use actual event slug, not "event"
- Search for: `ws/events/event` in frontend code

## How to Test

1. **Rebuild frontend** (already done):
   ```bash
   cd frontend && npm run build
   ```

2. **Restart backend** to load new endpoint:
   ```bash
   # Kill existing
   lsof -ti:8001 | xargs kill -9
   
   # Start fresh
   cd backend && PYTHONPATH=$PWD python -m uvicorn src.main:app --reload --port 8001
   ```

3. **Test in browser**:
   - Create event at http://localhost:3001/host/create
   - Navigate to dashboard
   - Create a question as attendee
   - Question should appear in host dashboard ✅

## Success Criteria

- ✅ No more `/api/v1/api/v1/` doubled paths
- ✅ EventSwitcher loads without 404
- ✅ Questions display correctly
- 🔍 Need to fix: Authorization headers
- 🔍 Need to fix: WebSocket slug issue

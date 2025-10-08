# T039: Manual Quickstart Validation - Testing Checklist

**Date:** 2025-10-08  
**Status:** 🧪 In Progress

---

## 🚀 Server Status

### Backend
- **URL:** http://localhost:8001
- **Health Check:** http://localhost:8001/api/v1/health
- **Status:** ✅ Running

### Frontend
- **URL:** http://localhost:3001
- **Status:** ✅ Running (switched from 3000)

---

## 📋 Test Scenarios

### **Scenario 1: Create Event with Custom Host Code**

**Objective:** Verify custom host code can be created and used for authentication

#### Steps:
1. [ ] Navigate to http://localhost:3001/host/create
2. [ ] Fill in event details:
   - Title: "Test Event 2025"
   - Slug: "test-event-2025"
   - Description: "Testing custom host codes"
3. [ ] ✅ Check "Use custom host code" checkbox
4. [ ] Enter custom host code: `host_test2025abc`
5. [ ] Verify character counter shows "17/17"
6. [ ] Submit form
7. [ ] Verify redirect to host dashboard
8. [ ] Verify host code displayed in purple box: `host_test2025abc`
9. [ ] Click copy button on host code
10. [ ] Verify toast notification: "Host code copied to clipboard!"

**Expected Results:**
- ✅ Event created with custom host code
- ✅ Dashboard accessible at `/host/dashboard/host_test2025abc`
- ✅ Host code displayed prominently in purple gradient box
- ✅ Copy functionality works

**API Verification:**
```bash
# Create event via API
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Test Event",
    "slug": "api-test-event",
    "host_code": "host_apitest1234"
  }'
```

---

### **Scenario 2: Duplicate Host Code Rejection**

**Objective:** Verify uniqueness constraint on host codes

#### Steps:
1. [ ] Navigate to http://localhost:3001/host/create
2. [ ] Fill in event details:
   - Title: "Duplicate Test"
   - Slug: "duplicate-test"
3. [ ] Check "Use custom host code"
4. [ ] Enter same host code: `host_test2025abc`
5. [ ] Submit form
6. [ ] Verify error message: "This host code is already in use..."

**Expected Results:**
- ❌ Event creation fails
- ✅ Error message displayed clearly
- ✅ Form remains filled (user doesn't lose data)

**API Verification:**
```bash
# Try to create duplicate
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Duplicate Event",
    "slug": "duplicate-event",
    "host_code": "host_apitest1234"
  }'
# Expected: 409 Conflict
```

---

### **Scenario 3: Invalid Host Code Format**

**Objective:** Verify format validation works

#### Steps:
1. [ ] Navigate to http://localhost:3001/host/create
2. [ ] Check "Use custom host code"
3. [ ] Try invalid formats:
   - [ ] Too short: `host_abc` (should show error on blur)
   - [ ] Missing prefix: `myevent123456` (should show error)
   - [ ] Wrong format: `host_UPPERCASE` (should auto-lowercase)
   - [ ] Special chars: `host_test@event` (should show error)
4. [ ] Verify error message: "Must be exactly 17 characters..."

**Expected Results:**
- ❌ Form validation prevents submission
- ✅ Inline error messages shown
- ✅ Auto-lowercase conversion works
- ✅ Format: `^host_[a-z0-9]{12}$` enforced

---

### **Scenario 4: EventSwitcher Pagination**

**Objective:** Verify EventSwitcher shows events and pagination works

#### Prerequisites:
- Create 3+ events with same host code

#### Steps:
1. [ ] Navigate to any host dashboard (e.g., `/host/dashboard/host_test2025abc`)
2. [ ] Locate EventSwitcher dropdown in header (left of event title)
3. [ ] Click dropdown button
4. [ ] Verify dropdown shows:
   - [ ] Header: "Your Events" with count
   - [ ] List of events with titles, slugs, creation dates
   - [ ] Question count badges (blue pill)
   - [ ] Current event highlighted in indigo
5. [ ] If >20 events exist:
   - [ ] Verify "Load More Events" button visible
   - [ ] Click "Load More"
   - [ ] Verify additional events loaded
6. [ ] Click a different event in list
7. [ ] Verify navigation to that event's dashboard
8. [ ] Verify URL changed to new host code
9. [ ] Verify dropdown closed after selection

**Expected Results:**
- ✅ Dropdown displays all events for host
- ✅ Pagination loads 20 at a time
- ✅ Current event highlighted
- ✅ Navigation works correctly

**Create Multiple Events:**
```bash
# Event 1
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"title": "Event One", "slug": "event-one", "host_code": "host_test2025abc"}'

# Event 2
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"title": "Event Two", "slug": "event-two", "host_code": "host_test2025abc"}'

# Event 3
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"title": "Event Three", "slug": "event-three", "host_code": "host_test2025abc"}'
```

---

### **Scenario 5: Question Highlight Animation**

**Objective:** Verify new questions are highlighted with yellow glow

#### Steps:
1. [ ] Navigate to attendee interface: http://localhost:3001/events/test-event-2025
2. [ ] Switch to "Questions & Answers" tab
3. [ ] Click "Ask Question" button
4. [ ] Enter question: "What time does the session start?"
5. [ ] Click "Submit Question"
6. [ ] Observe question card when it appears
7. [ ] Verify:
   - [ ] Question appears in list immediately
   - [ ] Yellow glow background visible (rgba(253, 230, 138))
   - [ ] Box shadow pulse effect
   - [ ] Glow fades over 2 seconds
   - [ ] Returns to white background after animation

**Expected Results:**
- ✅ Question submitted successfully
- ✅ Yellow highlight animation triggers immediately
- ✅ Animation duration: ~2 seconds
- ✅ Smooth fade-out to white

**Alternative Test:**
1. [ ] Refresh page immediately after submitting question (<5s)
2. [ ] Verify recent question still highlighted
3. [ ] Wait >5 seconds, refresh again
4. [ ] Verify no highlight on old questions

---

### **Scenario 6: WebSocket Reconnection**

**Objective:** Verify WebSocket automatically reconnects after network loss

#### Steps:
1. [ ] Navigate to http://localhost:3001/events/test-event-2025
2. [ ] Open browser DevTools → Network tab
3. [ ] Verify WebSocket connection established (Status: 101 Switching Protocols)
4. [ ] Stop backend server:
   ```bash
   # In terminal
   pkill -f "uvicorn src.main:app"
   ```
5. [ ] Observe console logs:
   - [ ] "WebSocket disconnected, will attempt to reconnect..."
   - [ ] "Reconnecting in 1000ms (attempt 1)..."
   - [ ] "Reconnecting in 2000ms (attempt 2)..."
6. [ ] Restart backend server:
   ```bash
   cd backend && PYTHONPATH=$(pwd) python -m uvicorn src.main:app --reload --port 8001
   ```
7. [ ] Observe console logs:
   - [ ] "WebSocket connected successfully"
8. [ ] Verify real-time updates resume

**Expected Results:**
- ✅ Connection loss detected automatically
- ✅ Exponential backoff: 1s → 2s → 4s → 8s (max 30s)
- ✅ Reconnection successful when server returns
- ✅ No manual refresh needed
- ✅ Real-time updates continue working

**Console Monitoring:**
```javascript
// Check WebSocket status in browser console
console.log('Connected:', window.ws?.connected);
```

---

### **Scenario 7: Host Dashboard Features**

**Objective:** Verify all host dashboard UI elements work correctly

#### Steps:
1. [ ] Navigate to host dashboard
2. [ ] Verify header layout:
   - [ ] EventSwitcher dropdown (left side)
   - [ ] Event title and slug
   - [ ] Host code box (purple gradient, lock icon)
   - [ ] Host code copy button
   - [ ] Attendee code (blue, copy button)
   - [ ] Event URL (green, copy button)
3. [ ] Click each copy button:
   - [ ] Host code → Toast: "Host code copied!"
   - [ ] Attendee code → Toast: "Attendee code copied!"
   - [ ] Event URL → Toast: "Event URL copied!"
4. [ ] Verify security warnings visible:
   - [ ] "Keep this private" on host code
   - [ ] "⚠️ Do NOT share your Host Code" in banner
5. [ ] Verify real-time connection indicator (if implemented)
6. [ ] Test tabs:
   - [ ] "Polls" tab
   - [ ] "Questions" tab

**Expected Results:**
- ✅ All elements render correctly
- ✅ Copy buttons work with visual feedback
- ✅ Security warnings prominent
- ✅ Layout responsive and clean

---

### **Scenario 8: Auto-Generated Host Code**

**Objective:** Verify automatic host code generation when not provided

#### Steps:
1. [ ] Navigate to http://localhost:3001/host/create
2. [ ] Fill in event details:
   - Title: "Auto Generated Event"
   - Slug: "auto-generated-event"
3. [ ] **Do NOT check** "Use custom host code"
4. [ ] Submit form
5. [ ] Verify redirect to dashboard
6. [ ] Observe host code in purple box
7. [ ] Verify format: `host_[random12chars]`
8. [ ] Verify host code is unique (not same as previous events)

**Expected Results:**
- ✅ Event created successfully
- ✅ Host code auto-generated
- ✅ Format correct: `^host_[a-z0-9]{12}$`
- ✅ Code is unique and random

---

### **Scenario 9: Case-Insensitive Host Code Handling**

**Objective:** Verify uppercase input is normalized to lowercase

#### Steps:
1. [ ] Navigate to http://localhost:3001/host/create
2. [ ] Check "Use custom host code"
3. [ ] Enter: `HOST_TESTCASE123` (uppercase)
4. [ ] Observe input field
5. [ ] Verify auto-conversion to: `host_testcase123`
6. [ ] Submit form
7. [ ] Verify event created with lowercase code

**Expected Results:**
- ✅ Uppercase automatically converted to lowercase
- ✅ Event created successfully
- ✅ Host code stored as lowercase

**API Verification:**
```bash
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Case Test",
    "slug": "case-test",
    "host_code": "HOST_UPPERCASE99"
  }'
# Should succeed with lowercase conversion
```

---

### **Scenario 10: Navigation & Routing**

**Objective:** Verify all routes work correctly

#### Steps:
1. [ ] Test route: `/` → Homepage
2. [ ] Test route: `/host/create` → Event creation form
3. [ ] Test route: `/host/dashboard/:host_code` → Host dashboard
4. [ ] Test route: `/events/:slug` → Attendee interface
5. [ ] Test invalid route: `/invalid-page` → 404 or redirect
6. [ ] Test route with missing params → Appropriate error
7. [ ] Browser back/forward buttons work correctly

**Expected Results:**
- ✅ All routes render correct components
- ✅ Navigation smooth and responsive
- ✅ No console errors
- ✅ State preserved during navigation

---

## 🐛 Issues Found

### Issue Template:
```markdown
**Issue #:** 
**Severity:** Critical / High / Medium / Low
**Scenario:** 
**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Behavior:**

**Actual Behavior:**

**Screenshots/Logs:**

**Status:** Open / Fixed / Won't Fix
```

---

## ✅ Test Results Summary

| Scenario | Status | Notes |
|----------|--------|-------|
| 1. Create Event with Custom Host Code | ⏳ Pending | |
| 2. Duplicate Host Code Rejection | ⏳ Pending | |
| 3. Invalid Host Code Format | ⏳ Pending | |
| 4. EventSwitcher Pagination | ⏳ Pending | |
| 5. Question Highlight Animation | ⏳ Pending | |
| 6. WebSocket Reconnection | ⏳ Pending | |
| 7. Host Dashboard Features | ⏳ Pending | |
| 8. Auto-Generated Host Code | ⏳ Pending | |
| 9. Case-Insensitive Handling | ⏳ Pending | |
| 10. Navigation & Routing | ⏳ Pending | |

---

## 📊 Coverage Assessment

### Features Tested:
- [ ] Custom host code creation (UI + API)
- [ ] Host code validation (format, uniqueness, case)
- [ ] EventSwitcher (dropdown, pagination, navigation)
- [ ] Question highlight animation (CSS, timing, detection)
- [ ] WebSocket reconnection (exponential backoff, auto-recovery)
- [ ] Host dashboard (layout, copy buttons, security warnings)
- [ ] Auto-generation fallback
- [ ] Routing and navigation

### Edge Cases:
- [ ] Empty form submission
- [ ] Network failures during submission
- [ ] Multiple rapid submissions
- [ ] Very long event titles/descriptions
- [ ] Special characters in inputs
- [ ] Browser refresh during operations
- [ ] Multiple browser tabs

---

## 🎯 Success Criteria

**T039 is COMPLETE when:**
- ✅ All 10 scenarios pass without critical issues
- ✅ Custom host code flow works end-to-end (create → authenticate → manage)
- ✅ EventSwitcher displays and navigates correctly
- ✅ Question highlight animation triggers and fades properly
- ✅ WebSocket reconnection handles network issues gracefully
- ✅ No TypeScript/runtime errors in console
- ✅ All UI copy buttons provide visual feedback
- ✅ API endpoints return correct status codes and data
- ✅ Database constraints enforced (uniqueness, format)
- ✅ Documentation updated with any discovered issues

---

## 🚀 Quick Start Commands

### Start Servers
```bash
# Terminal 1: Backend
cd backend && PYTHONPATH=$(pwd) python -m uvicorn src.main:app --reload --port 8001

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Test API Health
```bash
curl http://localhost:8001/api/v1/health
```

### Create Test Event
```bash
curl -X POST http://localhost:8001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Event", "slug": "test-event", "host_code": "host_quicktest99"}'
```

### Check Browser Console
- F12 → Console tab
- Look for WebSocket logs
- Check for React errors

---

## 📝 Notes

**Tester:** [Your Name]  
**Environment:** 
- macOS
- Chrome/Firefox/Safari [specify]
- Backend: Python 3.13.5
- Frontend: React 18, Vite 4.5.14

**Additional Observations:**
- 

---

**Last Updated:** 2025-10-08

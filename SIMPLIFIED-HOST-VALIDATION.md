# Simplified Host Code Validation

## Summary of Changes

Fixed two critical issues:
1. **CORS Configuration** - Added port 3001 to allowed origins
2. **Simplified Host Code Validation** - Made validation more user-friendly

## Changes Made

### 1. Backend: CORS Fix (`backend/src/core/config.py`)
**Problem**: Frontend running on port 3001 was blocked by CORS (OPTIONS 400 Bad Request)

**Solution**: Added ports 3001 to allowed_origins
```python
allowed_origins: list[str] = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
    "http://localhost:3001",  # ADDED
    "http://127.0.0.1:3001"   # ADDED
]
```

### 2. Backend: Simplified Validation (`backend/src/core/validation.py`)
**Before**: Required exact format `host_[a-z0-9]{12}` (exactly 17 characters)
- Example: `host_abc123def456`
- Very strict, confusing for users

**After**: Accept 3-30 alphanumeric characters + hyphens/underscores
- Examples: `myteam`, `my-team-2025`, `company_abc`
- Backend auto-prefixes with `host_` if not present
- Much more user-friendly

**Code Changes**:
```python
# Old pattern
HOST_CODE_PATTERN = re.compile(r'^host_[a-z0-9]{12}$')

# New pattern (simplified)
HOST_CODE_PATTERN = re.compile(r'^[a-z0-9_-]{3,30}$', re.IGNORECASE)

# Updated sanitize_host_code to auto-prefix
def sanitize_host_code(code: str) -> str:
    cleaned = code.strip().lower()
    if not cleaned.startswith('host_'):
        cleaned = f'host_{cleaned}'  # Auto-prefix
    return cleaned
```

### 3. Backend: Service & API Updates
**Files**: `backend/src/services/event_service.py`, `backend/src/api/events.py`

**Changes**:
- Updated error message: "Host code must be 3-30 characters (alphanumeric, hyphens, underscores only)"
- Updated API description to reflect new format
- Sanitization now happens after validation

### 4. Frontend: Simplified Validation (`frontend/src/App.tsx`)
**Changes**:
- Updated `validateHostCode()` function to match backend
- Changed placeholder from `host_abc123def456` to `myteam2025`
- Updated maxLength from 17 to 35 characters
- Updated help text to explain auto-prefixing
- Removed forced lowercase conversion (backend handles it)
- Updated error messages

**User-Facing Changes**:
- Input field now accepts human-friendly codes
- Clear message: "Backend will auto-prefix with 'host_'"
- Character counter shows actual input length
- No need to manually type `host_` prefix

## Testing

### Test Case 1: Simple Code
**Input**: `myteam`
**Result**: Backend converts to `host_myteam` ✅

### Test Case 2: With Hyphens
**Input**: `my-team-2025`
**Result**: Backend converts to `host_my-team-2025` ✅

### Test Case 3: Already Prefixed
**Input**: `host_existing`
**Result**: Kept as `host_existing` (no double prefix) ✅

### Test Case 4: Invalid (too short)
**Input**: `ab`
**Result**: Validation error: "Host code must be 3-30 characters..." ❌

### Test Case 5: Invalid (special chars)
**Input**: `my@team!`
**Result**: Validation error ❌

## Benefits

1. **User-Friendly**: No need to remember complex format
2. **Intuitive**: Use natural team/project names
3. **Backward Compatible**: Old `host_*` codes still work
4. **Consistent**: Backend handles all normalization
5. **Clear Errors**: Better validation messages

## Next Steps

Please test creating an event with a custom host code like:
- `myteam`
- `project-2025`
- `company_abc`

The application should now work without the "Failed to create event" error!

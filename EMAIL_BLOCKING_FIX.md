# Email Account Blocking Fix ✅

## Problem

System was blocking by **IP address** instead of **email account**. This meant:
- Multiple users from same IP could be affected
- User could bypass by changing IP
- Not tracking attacks per user account

## Solution

### 1. Always Look Up User by Email ✅

**Updated `backend/routers/auth.py`**:
- `log_failed_login_attempt()` now **always** looks up user by email
- Even if `user_id` is None, it finds the user from email
- Then tracks attacks for that user account

**Updated `backend/routers/admin_auth.py`**:
- `record_failed_login()` now looks up user by username/email
- Tracks attacks for the user account, not IP

**Updated `backend/attack_tracking.py`**:
- For unauthenticated attacks, tries to find user from alert metadata
- Extracts email from metadata and looks up user
- Recursively calls tracking with found user_id
- Only falls back to IP blocking if no user found

### 2. How It Works Now

```
User attempts login with SQL injection
    ↓
Backend receives email address
    ↓
Look up user_id from email (ALWAYS)
    ↓
Create security alert with user_id
    ↓
Track attack count for this user_id
    ↓
2+ attacks → Suspend user account (is_active = false)
10+ attacks → Ban user account + create ban record
    ↓
User cannot login (account blocked, not IP)
```

### 3. Key Changes

**Before**:
- Blocked by IP address
- Multiple users affected
- User could bypass with VPN

**After**:
- Blocks by email/user account
- Only the attacking user is affected
- User cannot bypass by changing IP
- Account is suspended/banned permanently

---

## Web Requests API Fix ✅

### Problem

Error: `'user_id'` - 500 Internal Server Error when fetching web requests

### Root Cause

1. Query structure issue with Supabase `select("*", count="exact")`
2. Missing field handling in response parsing
3. Column name mismatches

### Solution

**Updated `backend/routers/admin.py`**:
1. **Separated count and data queries** - Avoids Supabase query issues
2. **Explicit column selection** - Selects specific columns instead of `*`
3. **Better error handling** - Catches and logs specific errors
4. **Field validation** - Ensures all required fields exist with defaults
5. **Improved WebRequestResponse model** - Handles None values properly

**Changes**:
```python
# Before (problematic)
query = db.table("web_requests").select("*", count="exact")

# After (fixed)
base_query = db.table("web_requests")
# Apply filters...
count_result = base_query.select("request_id", count="exact").execute()
result = base_query.select("request_id, user_id, username, ...").execute()
```

---

## Testing

### Test Email Blocking

1. **Register user**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "attacker@test.com", "password": "Test123!", "role": "BUYER"}'
   ```

2. **Attack twice from different IPs** (should still suspend):
   ```bash
   # Attack 1 (from IP 1)
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "attacker@test.com", "password": "'"'"' OR 1=1 --"}'
   
   # Attack 2 (from different IP - use VPN or different network)
   # Should still suspend the account
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "attacker@test.com", "password": "admin'"'"' --"}'
   ```

3. **Verify account is suspended**:
   - Check Admin Dashboard → Users
   - Find `attacker@test.com`
   - Status should be "Suspended"
   - Attack count: 2

4. **Try to login** (should fail):
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "attacker@test.com", "password": "Test123!"}'
   ```
   Expected: 403 "Account has been suspended or deactivated"

### Test Web Requests

1. **Make some API requests** (they should be logged)
2. **Open Admin Dashboard** → Web Requests tab
3. **Should display**:
   - All requests in table
   - User info (if authenticated)
   - IP addresses
   - HTTP methods
   - Response status codes
   - Response times

---

## Verification

### Check User Status
```sql
SELECT user_id, email, is_active 
FROM users 
WHERE email = 'attacker@test.com';
-- Expected: is_active = false after 2 attacks
```

### Check Attack Count
```sql
SELECT COUNT(*) as attack_count
FROM security_alerts
WHERE user_id = (
  SELECT user_id FROM users WHERE email = 'attacker@test.com'
);
-- Expected: >= 2
```

### Check Web Requests Table
```sql
SELECT COUNT(*) FROM web_requests;
-- Should show number of logged requests
```

---

## Files Modified

1. **`backend/routers/auth.py`** ✅
   - Always looks up user by email
   - Tracks attacks for user account

2. **`backend/routers/admin_auth.py`** ✅
   - Looks up user by username/email
   - Tracks attacks for user account

3. **`backend/attack_tracking.py`** ✅
   - Tries to find user from email in metadata
   - Only blocks by IP if no user found

4. **`backend/routers/admin.py`** ✅
   - Fixed Web Requests query structure
   - Better error handling
   - Explicit column selection

---

## Important Notes

- ✅ **Blocking is now by email/user account**, not IP
- ✅ **User cannot bypass by changing IP**
- ✅ **Only the attacking user is affected**
- ✅ **Web Requests API should work now**
- ✅ **All errors are logged for debugging**

---

**Status**: ✅ Fixed - Blocking by email account, Web Requests API fixed
**Last Updated**: 2025-12-09


# Web Requests API Debug Guide

## Current Error

```
Failed to get web requests: 'user_id'
500 Internal Server Error
```

## Possible Causes

1. **Table doesn't exist** - `web_requests` table not created
2. **Column name mismatch** - Database column name different from code
3. **Query structure issue** - Supabase query syntax error
4. **Data format issue** - Response data format unexpected

## Debugging Steps

### Step 1: Verify Table Exists

Run in Supabase SQL Editor:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'web_requests';
```

**Expected columns**:
- `request_id` (bigint)
- `user_id` (bigint, nullable)
- `username` (varchar)
- `ip_address` (varchar)
- `http_method` (varchar)
- `path` (varchar)
- `endpoint` (varchar)
- `response_status` (integer)
- `response_time_ms` (integer)
- `is_authenticated` (boolean)
- `created_at` (timestamptz)

### Step 2: Check if Table Has Data

```sql
SELECT COUNT(*) FROM web_requests;
```

If 0, the middleware might not be logging requests.

### Step 3: Test Simple Query

```sql
SELECT request_id, user_id, ip_address 
FROM web_requests 
LIMIT 1;
```

If this fails, the table structure is wrong.

### Step 4: Check Backend Logs

```bash
tail -f backend/logs/application.log | grep -i "web.request\|error"
```

Look for:
- Table errors
- Query errors
- Column errors

### Step 5: Verify Middleware is Running

Check `backend/main.py`:
```python
app.add_middleware(WebRequestsMiddleware, exclude_paths=[...])
```

### Step 6: Test API Directly

```bash
# Get admin token first
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Then test web requests endpoint
curl -X GET "http://localhost:8000/api/admin/web-requests?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Quick Fixes

### Fix 1: Create Table if Missing

Run `backend/admin_logging_schema_safe.sql` in Supabase SQL Editor.

### Fix 2: Check Column Names

If columns are named differently, update the query:
```python
# Instead of user_id, might be user_id or userid
req_dict["user_id"] = req_data.get("user_id") or req_data.get("userid")
```

### Fix 3: Verify Middleware Logging

Make a test request:
```bash
curl http://localhost:8000/api/health
```

Then check:
```sql
SELECT * FROM web_requests ORDER BY created_at DESC LIMIT 1;
```

Should show the request.

### Fix 4: Simplify Query

If complex queries fail, try simplest query:
```python
result = db.table("web_requests").select("*").limit(10).execute()
```

## Current Implementation

The code now:
1. ✅ Checks if table exists
2. ✅ Handles errors gracefully
3. ✅ Returns empty result on error (doesn't crash)
4. ✅ Logs detailed errors
5. ✅ Uses safe field access with `.get()`

## Next Steps

1. **Check backend logs** for detailed error
2. **Verify table exists** in Supabase
3. **Test simple query** in SQL Editor
4. **Check middleware** is logging requests
5. **Restart backend** after fixes

---

**Status**: Debugging in progress
**Last Updated**: 2025-12-09


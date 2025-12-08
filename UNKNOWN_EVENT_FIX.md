# Unknown Event Issue - Fix Summary

## Problem
Tickets in "My Collection" were showing "Unknown Event" instead of the actual event name.

## Root Causes Identified

1. **Orphaned Tickets**: Tickets with `event_id` values that don't exist in the `events` table
2. **Event Matching Issues**: Frontend couldn't match ticket `event_id` with event `id` due to type mismatches or missing events
3. **Missing Event Fetching**: Events weren't being fetched individually when missing from the main events list

## Fixes Implemented

### 1. Backend Improvements (`backend/routers/tickets.py`)

- **Event Existence Validation**: Added batch checking to verify that all ticket `event_id` values actually exist in the events table
- **Better Logging**: Added warnings when tickets have invalid `event_id` values
- **Error Handling**: Improved error messages for debugging

```python
# Now validates event existence before returning tickets
# Logs warnings for orphaned tickets (tickets with event_id that don't exist)
```

### 2. Frontend Improvements (`frontend/pages/Dashboard.tsx`)

- **Improved Event Matching**: Enhanced matching logic with multiple strategies:
  - Direct numeric comparison (primary)
  - String comparison (fallback)
- **Parallel Event Fetching**: Missing events are now fetched in parallel for better performance
- **Better Error Handling**: More detailed logging to help identify matching issues
- **Robust Matching**: Handles type mismatches and edge cases

### 3. Diagnostic Tools

Created SQL scripts to help diagnose and fix issues:

- **`backend/diagnose_ticket_event_issue.sql`**: Diagnostic queries to identify:
  - Tickets with missing event_id
  - Orphaned tickets (event_id doesn't exist)
  - Type mismatches
  - Summary statistics

- **`backend/fix_orphaned_tickets.sql`**: Scripts to fix orphaned tickets:
  - Option A: Delete orphaned tickets (USE WITH CAUTION)
  - Option B: Set event_id to NULL (safer, preserves tickets)
  - Verification queries

## How to Use

### Step 1: Diagnose the Issue

Run the diagnostic SQL script in your Supabase SQL Editor:

```sql
-- Run: backend/diagnose_ticket_event_issue.sql
```

This will show you:
- Which tickets have missing events
- Event IDs in the database
- Summary of ticket/event relationships

### Step 2: Fix Orphaned Tickets (if needed)

If you find orphaned tickets, run the fix script:

```sql
-- Run: backend/fix_orphaned_tickets.sql
-- Review the queries and uncomment the appropriate fix option
```

**Recommended**: Use Option B (set event_id to NULL) to preserve tickets while fixing the issue.

### Step 3: Verify the Fix

1. Check backend logs for warnings about orphaned tickets
2. Check browser console for event matching logs
3. Verify that event names are now displayed correctly in "My Collection"

## Expected Behavior After Fix

1. **Valid Tickets**: Tickets with valid `event_id` should show the event name
2. **Orphaned Tickets**: Tickets with invalid `event_id` will show "Event #X" or "Unknown Event" (expected for deleted events)
3. **Missing Events**: If an event is missing from the main list, it will be fetched individually
4. **Better Logging**: Console logs will help identify any remaining issues

## Database Schema Notes

- **Events table**: Uses `event_id` as primary key (BIGSERIAL)
- **Tickets table**: Uses `event_id` to reference events (BIGINT, foreign key to events.event_id)
- **API Response**: Events API returns `id` field = `event_id` from database
- **API Response**: Tickets API returns `event_id` field directly from database

## Troubleshooting

If you still see "Unknown Event":

1. **Check Backend Logs**: Look for warnings about orphaned tickets
2. **Check Browser Console**: Look for event matching logs
3. **Run Diagnostic SQL**: Verify ticket/event relationships in database
4. **Check Event IDs**: Ensure events exist with the IDs referenced by tickets
5. **Clear Cache**: Events are cached for 2 minutes, tickets for 1 minute

## Prevention

To prevent this issue in the future:

1. **Foreign Key Constraints**: Ensure `tickets.event_id` has a proper foreign key constraint to `events.event_id`
2. **Cascade Deletes**: Consider CASCADE DELETE if events can be deleted (tickets will be deleted too)
3. **Validation**: Always validate event existence before creating tickets
4. **Monitoring**: Monitor backend logs for orphaned ticket warnings

## Files Modified

- `backend/routers/tickets.py` - Added event existence validation
- `frontend/pages/Dashboard.tsx` - Improved event matching and fetching
- `backend/diagnose_ticket_event_issue.sql` - New diagnostic script
- `backend/fix_orphaned_tickets.sql` - New fix script


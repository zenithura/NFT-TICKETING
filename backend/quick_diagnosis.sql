-- ============================================================================
-- QUICK DIAGNOSIS: Check if events 4, 5, 6 exist
-- ============================================================================
-- Run this in Supabase SQL Editor to quickly see what's in your database
-- ============================================================================

-- Check if events with IDs 4, 5, 6 exist
SELECT 
    'Events with IDs 4, 5, 6' as check_type,
    event_id,
    name,
    event_date,
    status
FROM events
WHERE event_id IN (4, 5, 6)
ORDER BY event_id;

-- Check all events
SELECT 
    'All Events' as check_type,
    event_id,
    name,
    event_date,
    status
FROM events
ORDER BY event_id;

-- Check tickets and their event_ids
SELECT 
    'Tickets' as check_type,
    ticket_id,
    event_id,
    owner_wallet_id,
    status
FROM tickets
ORDER BY ticket_id
LIMIT 20;

-- Check if tickets reference non-existent events
SELECT 
    t.ticket_id,
    t.event_id as ticket_event_id,
    e.event_id as event_exists,
    e.name as event_name,
    CASE 
        WHEN e.event_id IS NULL THEN '❌ EVENT MISSING'
        ELSE '✅ EVENT EXISTS'
    END as status
FROM tickets t
LEFT JOIN events e ON t.event_id = e.event_id
WHERE t.event_id IN (4, 5, 6)
ORDER BY t.ticket_id;


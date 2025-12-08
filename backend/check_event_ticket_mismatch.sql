-- ============================================================================
-- CHECK EVENT-TICKET MISMATCH
-- ============================================================================
-- This script helps identify tickets that reference events that don't exist
-- Run this in your Supabase SQL Editor to diagnose the issue
-- ============================================================================

-- 1. Check what events exist
SELECT 
    event_id,
    name as event_name,
    event_date,
    status
FROM events
ORDER BY event_id;

-- 2. Check what event_ids tickets are referencing
SELECT 
    ticket_id,
    event_id,
    owner_wallet_id,
    status as ticket_status,
    created_at
FROM tickets
ORDER BY ticket_id;

-- 3. Find tickets that reference non-existent events
SELECT 
    t.ticket_id,
    t.event_id,
    t.owner_wallet_id,
    t.status as ticket_status,
    CASE 
        WHEN e.event_id IS NULL THEN 'MISSING EVENT'
        ELSE e.name
    END as event_status
FROM tickets t
LEFT JOIN events e ON t.event_id = e.event_id
WHERE e.event_id IS NULL
ORDER BY t.ticket_id;

-- 4. Count tickets per event
SELECT 
    e.event_id,
    e.name as event_name,
    COUNT(t.ticket_id) as ticket_count
FROM events e
LEFT JOIN tickets t ON e.event_id = t.event_id
GROUP BY e.event_id, e.name
ORDER BY e.event_id;

-- 5. Summary: Total tickets vs events
SELECT 
    (SELECT COUNT(*) FROM tickets) as total_tickets,
    (SELECT COUNT(*) FROM events) as total_events,
    (SELECT COUNT(DISTINCT event_id) FROM tickets) as unique_event_ids_in_tickets,
    (SELECT COUNT(*) FROM tickets t LEFT JOIN events e ON t.event_id = e.event_id WHERE e.event_id IS NULL) as tickets_with_missing_events;


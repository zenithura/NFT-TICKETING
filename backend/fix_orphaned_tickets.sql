-- Fix orphaned tickets (tickets with event_id that don't exist in events table)
-- This script helps resolve "Unknown Event" issues

-- 1. First, identify orphaned tickets
SELECT 
    t.ticket_id,
    t.event_id,
    w.address as owner_address,
    'ORPHANED: event_id does not exist' as issue
FROM tickets t
LEFT JOIN events e ON t.event_id = e.event_id
LEFT JOIN wallets w ON t.owner_wallet_id = w.wallet_id
WHERE t.event_id IS NOT NULL 
    AND t.event_id != 0
    AND e.event_id IS NULL
ORDER BY t.ticket_id DESC;

-- 2. Option A: Delete orphaned tickets (USE WITH CAUTION - only if tickets are invalid)
-- Uncomment the following if you want to delete orphaned tickets:
-- DELETE FROM tickets 
-- WHERE event_id IS NOT NULL 
--     AND event_id != 0
--     AND event_id NOT IN (SELECT event_id FROM events);

-- 3. Option B: Set orphaned tickets' event_id to NULL (safer - preserves tickets)
-- This allows tickets to exist but they'll show as "Unknown Event"
-- Uncomment the following if you want to nullify orphaned event_ids:
-- UPDATE tickets 
-- SET event_id = NULL
-- WHERE event_id IS NOT NULL 
--     AND event_id != 0
--     AND event_id NOT IN (SELECT event_id FROM events);

-- 4. Option C: Find the correct event_id if tickets were created with wrong references
-- Check if there are events with similar names or dates that might match
-- This requires manual review

-- 5. Verify all tickets have valid event references after fix
SELECT 
    CASE 
        WHEN t.event_id IS NULL THEN 'NULL event_id'
        WHEN t.event_id = 0 THEN 'ZERO event_id'
        WHEN e.event_id IS NULL THEN 'ORPHANED'
        ELSE 'VALID'
    END as status,
    COUNT(*) as ticket_count,
    STRING_AGG(DISTINCT e.name, ', ') as event_names
FROM tickets t
LEFT JOIN events e ON t.event_id = e.event_id
GROUP BY 
    CASE 
        WHEN t.event_id IS NULL THEN 'NULL event_id'
        WHEN t.event_id = 0 THEN 'ZERO event_id'
        WHEN e.event_id IS NULL THEN 'ORPHANED'
        ELSE 'VALID'
    END;

-- 6. List all events with their ticket counts
SELECT 
    e.event_id,
    e.name,
    e.status,
    COUNT(t.ticket_id) as ticket_count
FROM events e
LEFT JOIN tickets t ON e.event_id = t.event_id
GROUP BY e.event_id, e.name, e.status
ORDER BY e.event_id DESC;


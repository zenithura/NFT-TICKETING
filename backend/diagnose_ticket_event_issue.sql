-- Diagnostic query to find tickets with missing events
-- This will help identify why "Unknown Event" is showing

-- 1. Find all tickets and their event_id values
SELECT 
    t.ticket_id,
    t.event_id,
    t.owner_wallet_id,
    w.address as owner_address,
    CASE 
        WHEN t.event_id IS NULL THEN 'NULL event_id'
        WHEN t.event_id = 0 THEN 'event_id is 0'
        ELSE 'Has event_id'
    END as event_id_status
FROM tickets t
LEFT JOIN wallets w ON t.owner_wallet_id = w.wallet_id
ORDER BY t.ticket_id DESC
LIMIT 20;

-- 2. Find tickets with event_id that don't exist in events table
SELECT 
    t.ticket_id,
    t.event_id,
    w.address as owner_address,
    'ORPHANED: event_id does not exist in events table' as issue
FROM tickets t
LEFT JOIN events e ON t.event_id = e.event_id
LEFT JOIN wallets w ON t.owner_wallet_id = w.wallet_id
WHERE t.event_id IS NOT NULL 
    AND t.event_id != 0
    AND e.event_id IS NULL
ORDER BY t.ticket_id DESC;

-- 3. Find all events and their IDs
SELECT 
    e.event_id,
    e.name,
    e.status,
    COUNT(t.ticket_id) as ticket_count
FROM events e
LEFT JOIN tickets t ON e.event_id = t.event_id
GROUP BY e.event_id, e.name, e.status
ORDER BY e.event_id DESC;

-- 4. Check for type mismatches (event_id as string vs integer)
SELECT 
    'Tickets with non-numeric event_id' as check_type,
    COUNT(*) as count
FROM tickets
WHERE event_id IS NOT NULL 
    AND event_id::text !~ '^[0-9]+$';

-- 5. Summary: Count tickets by event_id status
SELECT 
    CASE 
        WHEN t.event_id IS NULL THEN 'NULL'
        WHEN t.event_id = 0 THEN 'ZERO'
        WHEN e.event_id IS NULL THEN 'ORPHANED'
        ELSE 'VALID'
    END as status,
    COUNT(*) as ticket_count
FROM tickets t
LEFT JOIN events e ON t.event_id = e.event_id
GROUP BY 
    CASE 
        WHEN t.event_id IS NULL THEN 'NULL'
        WHEN t.event_id = 0 THEN 'ZERO'
        WHEN e.event_id IS NULL THEN 'ORPHANED'
        ELSE 'VALID'
    END;


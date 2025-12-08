-- ============================================================================
-- FIX TICKET EVENT REFERENCES
-- ============================================================================
-- This script helps fix tickets that reference non-existent events
-- OPTION 1: Create placeholder events for missing event_ids
-- OPTION 2: Update tickets to reference existing events
-- OPTION 3: Delete tickets with invalid event references
-- ============================================================================

-- STEP 1: First, run check_event_ticket_mismatch.sql to see what's wrong

-- ============================================================================
-- OPTION 1: Create placeholder events for tickets that reference missing events
-- ============================================================================
-- This creates events with IDs 4, 5, 6 if they don't exist
-- Adjust the event details as needed

INSERT INTO events (
    event_id,
    venue_id,
    name,
    description,
    event_date,
    start_time,
    end_time,
    total_supply,
    available_tickets,
    base_price,
    status,
    organizer_address
)
SELECT 
    missing_event_id,
    1, -- Default venue_id (adjust if needed)
    'Event ' || missing_event_id, -- Placeholder name
    'This event was created to fix ticket references', -- Placeholder description
    NOW() + INTERVAL '30 days', -- Default date
    '18:00:00'::TIME, -- Default start time
    '22:00:00'::TIME, -- Default end time
    100, -- Default total supply
    100, -- Default available tickets
    0.1, -- Default price
    'UPCOMING'::event_status, -- Default status
    '0x0000000000000000000000000000000000000000' -- Default organizer
FROM (
    SELECT DISTINCT t.event_id as missing_event_id
    FROM tickets t
    LEFT JOIN events e ON t.event_id = e.event_id
    WHERE e.event_id IS NULL
    AND t.event_id IS NOT NULL
) missing_events
WHERE NOT EXISTS (
    SELECT 1 FROM events e2 WHERE e2.event_id = missing_events.missing_event_id
)
ON CONFLICT (event_id) DO NOTHING;

-- ============================================================================
-- OPTION 2: Update tickets to reference an existing event
-- ============================================================================
-- This updates tickets with invalid event_id to reference the first available event
-- WARNING: This will change ticket ownership associations!

/*
UPDATE tickets t
SET event_id = (
    SELECT event_id FROM events 
    ORDER BY event_id 
    LIMIT 1
)
WHERE NOT EXISTS (
    SELECT 1 FROM events e WHERE e.event_id = t.event_id
)
AND t.event_id IS NOT NULL;
*/

-- ============================================================================
-- OPTION 3: Delete tickets with invalid event references
-- ============================================================================
-- WARNING: This permanently deletes tickets!
-- Only use if you're sure these tickets are invalid

/*
DELETE FROM tickets
WHERE event_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM events e WHERE e.event_id = tickets.event_id
);
*/

-- ============================================================================
-- VERIFY THE FIX
-- ============================================================================
-- After running Option 1, verify that all tickets now have valid event references

SELECT 
    'Tickets with valid events' as status,
    COUNT(*) as count
FROM tickets t
INNER JOIN events e ON t.event_id = e.event_id

UNION ALL

SELECT 
    'Tickets with missing events' as status,
    COUNT(*) as count
FROM tickets t
LEFT JOIN events e ON t.event_id = e.event_id
WHERE e.event_id IS NULL;


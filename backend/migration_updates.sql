-- ============================================================================
-- NFT TICKETING PLATFORM - MIGRATION UPDATES
-- ============================================================================
-- This file contains ONLY new additions/updates needed for existing database
-- Run this in your Supabase SQL Editor AFTER the main schema is set up
-- ============================================================================

-- ============================================================================
-- PART 1: ADD MISSING COLUMNS
-- ============================================================================

-- Add organizer_address to events table (if not exists)
ALTER TABLE events 
ADD COLUMN IF NOT EXISTS organizer_address VARCHAR(255);

-- ============================================================================
-- PART 2: ADD MISSING INDEXES
-- ============================================================================

-- Index for events organizer_address (for faster organizer queries)
CREATE INDEX IF NOT EXISTS idx_events_organizer_address ON events(organizer_address);

-- ============================================================================
-- PART 3: VERIFY TICKETS TABLE STRUCTURE
-- ============================================================================
-- IMPORTANT: Ensure tickets table uses owner_wallet_id (NOT owner_address)
-- 
-- If your tickets table has owner_address instead of owner_wallet_id,
-- you need to migrate the data. This is a complex operation.
-- 
-- To check your current tickets table structure, run:
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'tickets' 
-- ORDER BY ordinal_position;
--
-- Expected columns for tickets table:
-- - ticket_id (BIGSERIAL PRIMARY KEY)
-- - event_id (BIGINT, references events)
-- - owner_wallet_id (BIGINT, references wallets)  <-- MUST BE THIS, NOT owner_address
-- - token_id (VARCHAR(255), UNIQUE, NOT NULL)
-- - nft_metadata_uri (VARCHAR(500))
-- - seat_number (VARCHAR(50))
-- - tier (ticket_tier enum)
-- - purchase_price (NUMERIC(18, 8))
-- - status (ticket_status enum)
-- - minted_at (TIMESTAMPTZ)
-- - last_transfer_at (TIMESTAMPTZ)
-- - created_at (TIMESTAMPTZ)
-- - updated_at (TIMESTAMPTZ)
-- ============================================================================

-- ============================================================================
-- PART 4: VERIFICATION QUERIES
-- ============================================================================
-- Uncomment and run these to verify your database structure:

-- Check if tickets table has owner_wallet_id (correct) or owner_address (wrong)
-- SELECT 
--     column_name, 
--     data_type,
--     is_nullable
-- FROM information_schema.columns 
-- WHERE table_name = 'tickets' 
--   AND (column_name = 'owner_wallet_id' OR column_name = 'owner_address')
-- ORDER BY column_name;

-- Check if events table has organizer_address
-- SELECT 
--     column_name, 
--     data_type
-- FROM information_schema.columns 
-- WHERE table_name = 'events' 
--   AND column_name = 'organizer_address';

-- Check if wallets table exists (required for tickets.owner_wallet_id)
-- SELECT EXISTS (
--     SELECT FROM information_schema.tables 
--     WHERE table_schema = 'public' 
--     AND table_name = 'wallets'
-- );

-- ============================================================================
-- PART 5: DATA MIGRATION (ONLY IF NEEDED)
-- ============================================================================
-- 
-- WARNING: Only run this section if your tickets table currently uses
-- owner_address instead of owner_wallet_id. This will migrate the data.
--
-- Step 1: Create wallets for all unique owner_addresses in tickets
-- INSERT INTO wallets (address, balance, allowlist_status, blacklisted)
-- SELECT DISTINCT 
--     owner_address as address,
--     0 as balance,
--     FALSE as allowlist_status,
--     FALSE as blacklisted
-- FROM tickets
-- WHERE owner_address IS NOT NULL
--   AND owner_address NOT IN (SELECT address FROM wallets)
-- ON CONFLICT (address) DO NOTHING;
--
-- Step 2: Add owner_wallet_id column to tickets (if it doesn't exist)
-- ALTER TABLE tickets 
-- ADD COLUMN IF NOT EXISTS owner_wallet_id BIGINT REFERENCES wallets(wallet_id);
--
-- Step 3: Populate owner_wallet_id from owner_address
-- UPDATE tickets t
-- SET owner_wallet_id = w.wallet_id
-- FROM wallets w
-- WHERE t.owner_address = w.address
--   AND t.owner_wallet_id IS NULL;
--
-- Step 4: Make owner_wallet_id NOT NULL (after data is migrated)
-- ALTER TABLE tickets 
-- ALTER COLUMN owner_wallet_id SET NOT NULL;
--
-- Step 5: Drop owner_address column (after verifying owner_wallet_id works)
-- ALTER TABLE tickets 
-- DROP COLUMN IF EXISTS owner_address;
--
-- Step 6: Add foreign key constraint (if not already exists)
-- ALTER TABLE tickets 
-- ADD CONSTRAINT tickets_owner_wallet_id_fkey 
-- FOREIGN KEY (owner_wallet_id) REFERENCES wallets(wallet_id) ON DELETE CASCADE;
-- ============================================================================

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
-- 
-- SUMMARY OF CHANGES:
-- 1. Added organizer_address column to events table
-- 2. Added index for organizer_address queries
-- 3. Verification queries to check database structure
-- 4. Optional data migration script (only if tickets uses owner_address)
--
-- NEXT STEPS:
-- 1. Run this migration file
-- 2. Run the verification queries to check your structure
-- 3. If tickets table uses owner_address, follow the migration steps in PART 5
-- 4. Verify all indexes are created
-- ============================================================================


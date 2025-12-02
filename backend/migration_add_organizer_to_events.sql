-- ============================================================================
-- MIGRATION: Add organizer_address column to events table
-- ============================================================================
-- This migration adds organizer_address column to track which organizer created the event
-- Run this in your Supabase SQL Editor
-- ============================================================================

-- Add organizer_address column to events table
ALTER TABLE events 
ADD COLUMN IF NOT EXISTS organizer_address VARCHAR(255);

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_events_organizer_address ON events(organizer_address);

-- Add comment
COMMENT ON COLUMN events.organizer_address IS 'Wallet address or email of the event organizer';

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Run this to verify the column was added:
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'events' AND column_name = 'organizer_address';


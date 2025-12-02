-- ============================================================================
-- RESALE SYSTEM MIGRATION
-- ============================================================================
-- This migration adds support for ticket resale with 50% max markup validation
-- Run this in your Supabase SQL Editor
-- ============================================================================

-- Add original_price column to marketplace table to track purchase price
ALTER TABLE marketplace 
ADD COLUMN IF NOT EXISTS original_price NUMERIC(18, 8) CHECK (original_price >= 0);

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_marketplace_original_price ON marketplace(original_price);

-- Add comment
COMMENT ON COLUMN marketplace.original_price IS 'Original purchase price of the ticket (used for markup validation)';

-- Update existing marketplace entries to have original_price = price (if null)
-- This is safe because we're just setting a default for existing data
UPDATE marketplace 
SET original_price = price 
WHERE original_price IS NULL;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================


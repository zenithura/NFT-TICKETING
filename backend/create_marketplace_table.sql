-- ============================================================================
-- CREATE MARKETPLACE TABLE FOR RESALE SYSTEM
-- ============================================================================
-- This SQL creates the marketplace table with original_price column
-- Run this in your Supabase SQL Editor
-- ============================================================================

-- Create marketplace table if it doesn't exist
-- FIXED: ticket_id changed from INTEGER to BIGINT to match tickets.ticket_id
CREATE TABLE IF NOT EXISTS marketplace (
    id SERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL,  -- FIXED: Changed from INTEGER to BIGINT to match tickets.ticket_id
    seller_address VARCHAR(255) NOT NULL,
    price NUMERIC(18, 8) NOT NULL CHECK (price >= 0),
    original_price NUMERIC(18, 8) CHECK (original_price >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'sold', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key constraints if tickets table exists
-- Check which column exists in tickets table and add appropriate constraint
DO $$ 
BEGIN
    -- Check if tickets table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tickets' AND table_schema = 'public') THEN
        -- Check if tickets table has ticket_id column (complete schema)
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'tickets' AND column_name = 'ticket_id' AND table_schema = 'public'
        ) THEN
            -- Add foreign key to tickets(ticket_id) - for complete schema
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'marketplace_ticket_id_fkey' 
                AND table_name = 'marketplace' AND table_schema = 'public'
            ) THEN
                BEGIN
                    ALTER TABLE marketplace 
                    ADD CONSTRAINT marketplace_ticket_id_fkey 
                    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE;
                EXCEPTION
                    WHEN duplicate_object THEN NULL;
                    WHEN undefined_table THEN NULL;
                    WHEN invalid_foreign_key THEN NULL;
                END;
            END IF;
        -- Check if tickets table has id column (simple schema)
        ELSIF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'tickets' AND column_name = 'id' AND table_schema = 'public'
        ) THEN
            -- Add foreign key to tickets(id) - for simple schema
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'marketplace_ticket_id_fkey' 
                AND table_name = 'marketplace' AND table_schema = 'public'
            ) THEN
                BEGIN
                    ALTER TABLE marketplace 
                    ADD CONSTRAINT marketplace_ticket_id_fkey 
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE;
                EXCEPTION
                    WHEN duplicate_object THEN NULL;
                    WHEN undefined_table THEN NULL;
                    WHEN invalid_foreign_key THEN NULL;
                END;
            END IF;
        END IF;
    END IF;
END $$;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_marketplace_ticket_id ON marketplace(ticket_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_seller_address ON marketplace(seller_address);
CREATE INDEX IF NOT EXISTS idx_marketplace_status ON marketplace(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_original_price ON marketplace(original_price);

-- Enable Row Level Security (RLS)
ALTER TABLE marketplace ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access
DROP POLICY IF EXISTS "Allow public read access on marketplace" ON marketplace;
CREATE POLICY "Allow public read access on marketplace" ON marketplace 
FOR SELECT USING (true);

-- Add comment
COMMENT ON TABLE marketplace IS 'Secondary market resale listings for tickets';
COMMENT ON COLUMN marketplace.original_price IS 'Original purchase price of the ticket (used for 50% max markup validation)';

-- ============================================================================
-- END OF MARKETPLACE TABLE CREATION
-- ============================================================================


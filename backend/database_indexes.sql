-- ============================================================================
-- DATABASE PERFORMANCE INDEXES
-- ============================================================================
-- This SQL creates indexes for frequently queried columns to improve query performance
-- Run this in your Supabase SQL Editor
-- ============================================================================

-- Events table indexes
CREATE INDEX IF NOT EXISTS idx_events_organizer_address ON events(organizer_address);
CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_venue_id ON events(venue_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC);

-- Tickets table indexes
CREATE INDEX IF NOT EXISTS idx_tickets_event_id ON tickets(event_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);

-- Conditional indexes based on schema (check which columns exist)
-- For complete schema (with owner_wallet_id)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'owner_wallet_id' AND table_schema = 'public'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_tickets_owner_wallet_id ON tickets(owner_wallet_id);
    END IF;
END $$;

-- For simple schema (with owner_address)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'owner_address' AND table_schema = 'public'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_tickets_owner_address ON tickets(owner_address);
    END IF;
END $$;

-- Token ID indexes (check which column exists)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'token_id' AND table_schema = 'public'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_tickets_token_id ON tickets(token_id) WHERE token_id IS NOT NULL;
    END IF;
END $$;

DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'nft_token_id' AND table_schema = 'public'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_tickets_nft_token_id ON tickets(nft_token_id) WHERE nft_token_id IS NOT NULL;
    END IF;
END $$;

-- Marketplace table indexes (already exists in create_marketplace_table.sql, but ensuring they're present)
CREATE INDEX IF NOT EXISTS idx_marketplace_ticket_id ON marketplace(ticket_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_seller_address ON marketplace(seller_address);
CREATE INDEX IF NOT EXISTS idx_marketplace_status ON marketplace(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_created_at ON marketplace(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_marketplace_price ON marketplace(price);

-- Venues table indexes
CREATE INDEX IF NOT EXISTS idx_venues_name ON venues(name);
CREATE INDEX IF NOT EXISTS idx_venues_location ON venues(location);
CREATE INDEX IF NOT EXISTS idx_venues_city ON venues(city);

-- Wallets table indexes
CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address);
CREATE INDEX IF NOT EXISTS idx_wallets_blacklisted ON wallets(blacklisted) WHERE blacklisted = true;

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_events_organizer_status ON events(organizer_address, status);
CREATE INDEX IF NOT EXISTS idx_tickets_event_status ON tickets(event_id, status);
CREATE INDEX IF NOT EXISTS idx_marketplace_status_ticket ON marketplace(status, ticket_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_seller_status ON marketplace(seller_address, status);

-- Conditional composite index for tickets (based on schema)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'owner_wallet_id' AND table_schema = 'public'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_tickets_event_owner_wallet ON tickets(event_id, owner_wallet_id);
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'owner_address' AND table_schema = 'public'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_tickets_event_owner_address ON tickets(event_id, owner_address);
    END IF;
END $$;

-- Partial indexes for active listings (most common query)
CREATE INDEX IF NOT EXISTS idx_marketplace_active_listings ON marketplace(ticket_id, price, created_at) WHERE status = 'active';

-- ============================================================================
-- END OF DATABASE INDEXES
-- ============================================================================


-- ============================================================================
-- FIX MARKETPLACE TABLE SCHEMA - DATA TYPE MISMATCH CORRECTION
-- ============================================================================
-- This SQL fixes the data type mismatch between marketplace.ticket_id (INTEGER)
-- and tickets.ticket_id (BIGINT) from your actual schema
-- ============================================================================

-- Step 1: Check current state
DO $$
BEGIN
    RAISE NOTICE 'Checking marketplace table structure...';
END $$;

-- Step 2: Fix ticket_id column type (if it's INTEGER, change to BIGINT)
DO $$
BEGIN
    -- Check if ticket_id is INTEGER and needs to be changed to BIGINT
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'marketplace' 
        AND column_name = 'ticket_id' 
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        RAISE NOTICE 'Converting marketplace.ticket_id from INTEGER to BIGINT...';
        ALTER TABLE marketplace 
            ALTER COLUMN ticket_id TYPE BIGINT;
        RAISE NOTICE 'Successfully converted ticket_id to BIGINT';
    ELSE
        RAISE NOTICE 'ticket_id is already BIGINT or column does not exist';
    END IF;
END $$;

-- Step 3: Fix id column type (optional, for consistency)
DO $$
BEGIN
    -- Check if id is INTEGER and we want to change it to BIGINT
    -- Note: This is optional - your schema shows it as integer, which works fine
    -- Uncomment if you want consistency with other tables
    /*
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'marketplace' 
        AND column_name = 'id' 
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        RAISE NOTICE 'Converting marketplace.id from INTEGER to BIGINT...';
        -- Need to recreate sequence
        CREATE SEQUENCE IF NOT EXISTS marketplace_id_seq_big;
        ALTER TABLE marketplace 
            ALTER COLUMN id TYPE BIGINT,
            ALTER COLUMN id SET DEFAULT nextval('marketplace_id_seq_big');
        ALTER SEQUENCE marketplace_id_seq_big OWNED BY marketplace.id;
        RAISE NOTICE 'Successfully converted id to BIGINT';
    END IF;
    */
END $$;

-- Step 4: Recreate foreign key constraint with correct types
DO $$
BEGIN
    -- Drop existing constraint if it exists (it may be invalid due to type mismatch)
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'marketplace_ticket_id_fkey' 
        AND table_name = 'marketplace' 
        AND table_schema = 'public'
    ) THEN
        RAISE NOTICE 'Dropping existing foreign key constraint...';
        ALTER TABLE marketplace DROP CONSTRAINT IF EXISTS marketplace_ticket_id_fkey;
    END IF;
    
    -- Recreate constraint with correct types
    -- Check which column exists in tickets table
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' 
        AND column_name = 'ticket_id' 
        AND table_schema = 'public'
    ) THEN
        RAISE NOTICE 'Creating foreign key constraint to tickets(ticket_id)...';
        ALTER TABLE marketplace 
            ADD CONSTRAINT marketplace_ticket_id_fkey 
            FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE;
        RAISE NOTICE 'Foreign key constraint created successfully';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' 
        AND column_name = 'id' 
        AND table_schema = 'public'
    ) THEN
        RAISE NOTICE 'Creating foreign key constraint to tickets(id)...';
        ALTER TABLE marketplace 
            ADD CONSTRAINT marketplace_ticket_id_fkey 
            FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE;
        RAISE NOTICE 'Foreign key constraint created successfully';
    ELSE
        RAISE WARNING 'Could not find tickets table or primary key column';
    END IF;
END $$;

-- Step 5: Verify the fix
DO $$
DECLARE
    ticket_id_type TEXT;
    tickets_pk_type TEXT;
BEGIN
    -- Get marketplace.ticket_id type
    SELECT data_type INTO ticket_id_type
    FROM information_schema.columns 
    WHERE table_name = 'marketplace' 
    AND column_name = 'ticket_id' 
    AND table_schema = 'public';
    
    -- Get tickets primary key type
    SELECT data_type INTO tickets_pk_type
    FROM information_schema.columns 
    WHERE table_name = 'tickets' 
    AND column_name IN ('ticket_id', 'id')
    AND table_schema = 'public'
    LIMIT 1;
    
    RAISE NOTICE 'Verification:';
    RAISE NOTICE '  marketplace.ticket_id type: %', ticket_id_type;
    RAISE NOTICE '  tickets primary key type: %', tickets_pk_type;
    
    IF ticket_id_type = tickets_pk_type THEN
        RAISE NOTICE '✅ Types match! Foreign key constraint should work.';
    ELSE
        RAISE WARNING '❌ Types do not match! Foreign key constraint may fail.';
    END IF;
END $$;

-- ============================================================================
-- END OF FIX
-- ============================================================================


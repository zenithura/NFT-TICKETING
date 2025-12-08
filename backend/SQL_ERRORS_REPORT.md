# SQL Errors and Issues Report

## Critical Issues Found

### 1. **Data Type Mismatch: marketplace.ticket_id**

**Location:** `backend/create_marketplace_table.sql` line 11

**Problem:**
- `marketplace.ticket_id` is defined as `INTEGER`
- `tickets.ticket_id` (from your schema) is `BIGINT`
- This causes foreign key constraint failures and potential data loss

**Current Code:**
```sql
CREATE TABLE IF NOT EXISTS marketplace (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL,  -- ❌ WRONG: Should be BIGINT
    ...
);
```

**Your Schema Shows:**
```sql
CREATE TABLE public.tickets (
  ticket_id bigint NOT NULL,  -- ✅ This is BIGINT
  ...
);
```

**Fix Required:**
```sql
ticket_id BIGINT NOT NULL,  -- ✅ Should match tickets.ticket_id type
```

### 2. **Data Type Mismatch: marketplace.id**

**Location:** `backend/create_marketplace_table.sql` line 10

**Problem:**
- `marketplace.id` is `SERIAL` (which creates INTEGER)
- Your schema shows `marketplace.id` as `integer`
- While this works, it's inconsistent with other tables that use BIGSERIAL/BIGINT
- For consistency and future scalability, should be BIGINT

**Current Code:**
```sql
id SERIAL PRIMARY KEY,  -- Creates INTEGER
```

**Your Schema Shows:**
```sql
id integer NOT NULL DEFAULT nextval('marketplace_id_seq'::regclass),
```

**Recommendation:**
```sql
id BIGSERIAL PRIMARY KEY,  -- For consistency with other tables
```

### 3. **Foreign Key Constraint Issue**

**Location:** `backend/create_marketplace_table.sql` lines 37-39, 58-60

**Problem:**
The foreign key constraint will fail if `ticket_id` types don't match:
- If `tickets.ticket_id` is `BIGINT` and `marketplace.ticket_id` is `INTEGER`, PostgreSQL will reject the foreign key

**Error You'll See:**
```
ERROR: foreign key constraint "marketplace_ticket_id_fkey" cannot be implemented
DETAIL: Key columns "ticket_id" and "ticket_id" are of incompatible types: integer and bigint.
```

## Minor Issues

### 4. **Missing Currency Column in marketplace**

**Location:** Your schema shows marketplace doesn't have `currency`, but events table has it

**Note:** This may be intentional, but worth checking if marketplace should track currency.

### 5. **Index on Wrong Column Type**

**Location:** `backend/database_indexes.sql` line 65

**Problem:**
If `ticket_id` is changed to BIGINT, the index will work, but the type mismatch should be fixed first.

## Recommended Fixes

### Fix 1: Update marketplace table creation

```sql
-- Fix the marketplace table definition
CREATE TABLE IF NOT EXISTS marketplace (
    id BIGSERIAL PRIMARY KEY,  -- Changed from SERIAL
    ticket_id BIGINT NOT NULL,  -- Changed from INTEGER to match tickets.ticket_id
    seller_address VARCHAR(255) NOT NULL,
    price NUMERIC(18, 8) NOT NULL CHECK (price >= 0),
    original_price NUMERIC(18, 8) CHECK (original_price >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'sold', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Fix 2: Migration script for existing tables

If the marketplace table already exists with wrong types, you'll need:

```sql
-- Migration to fix existing marketplace table
ALTER TABLE marketplace 
    ALTER COLUMN ticket_id TYPE BIGINT,
    ALTER COLUMN id TYPE BIGINT;
```

## Verification

To verify your current schema matches:

```sql
-- Check marketplace table structure
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'marketplace' 
    AND table_schema = 'public'
ORDER BY ordinal_position;

-- Check tickets table structure
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'tickets' 
    AND table_schema = 'public'
ORDER BY ordinal_position;

-- Check foreign key constraints
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'marketplace';
```

## Summary

**Critical:** Fix the `ticket_id` type mismatch immediately - this will cause foreign key constraint failures.

**Important:** Consider changing `id` to BIGINT for consistency.

**Status:** All other SQL files appear to be syntactically correct, but the type mismatch is a blocking issue.


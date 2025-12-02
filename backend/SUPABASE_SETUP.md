# Supabase Database Initialization Guide

## Quick Setup

1. **Open Supabase SQL Editor**
   - Go to: https://kuupyybybbvviupflpgj.supabase.co
   - Navigate to: SQL Editor (in left sidebar)

2. **Run the Schema**
   - Open [`supabase_schema.sql`](file:///home/eniac/Desktop/projects/new_version/duckdb/my_tests/backend/supabase_schema.sql) in this project
   - Copy all the SQL code
   - Paste into Supabase SQL Editor
   - Click "Run" or press Ctrl+Enter

3. **Verify Tables Created**
   - Go to: Table Editor (in left sidebar)
   - You should see 4 tables:
     - `users`
     - `events`
     - `tickets`
     - `marketplace`

## Schema Overview

### Tables Created

| Table | Description | Key Fields |
|-------|-------------|-----------|
| **users** | User accounts linked to wallet addresses | `address` (PK), `role`, `created_at` |
| **events** | Events created by organizers | `id`, `organizer_address`, `name`, `date`, `price` |
| **tickets** | Individual tickets for events | `id`, `event_id`, `owner_address`, `status` |
| **marketplace** | Ticket listings for resale | `id`, `ticket_id`, `seller_address`, `price`, `status` |

### Features Included

✅ Primary keys and foreign key relationships  
✅ Check constraints for data validation  
✅ Indexes for query performance  
✅ Row Level Security (RLS) enabled  
✅ Public read access policies  
✅ Demo data (2 sample users)

## Testing the Database

After running the schema, you can test it directly in Supabase:

1. Go to Table Editor
2. Click on `users` table
3. You should see 2 demo users:
   - `0x1234567890123456789012345678901234567890` (organizer)
   - `0x0987654321098765432109876543210987654321` (user)

## Using with Backend

Once the schema is initialized, your backend at http://localhost:8000 will be able to:

- Create and manage users
- Create events
- Mint and transfer tickets
- Handle marketplace listings
- Process ticket purchases

All operations will be persisted to your Supabase database.

## Troubleshooting

If you encounter errors:

1. **"relation already exists"** - Tables are already created, schema has run before
2. **Connection errors** - Verify your Supabase URL and keys in `backend/.env`
3. **Permission issues** - Ensure you're using the service_role key for admin operations

## Next Steps

After initializing the database:

1. Start the backend: `cd backend && uvicorn main:app --reload`
2. Test API at: http://localhost:8000/docs
3. Connect frontend to backend
4. Test wallet connection and user creation

# File header: Database schema verification script for tickets table.
# Checks if transaction_hash column exists in Supabase tickets table.

#!/usr/bin/env python3
"""Check if transaction_hash column exists in tickets table"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Purpose: Load environment variables from .env file.
# Side effects: Reads .env file, sets environment variables.
load_dotenv()

# Purpose: Retrieve Supabase connection credentials from environment.
# Side effects: Reads environment variables.
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Purpose: Initialize Supabase client connection.
# Side effects: Creates database client instance.
supabase = create_client(url, key)

# Purpose: Verify transaction_hash column exists by attempting to query it.
# Side effects: Executes database query, prints result or error message.
try:
    result = supabase.table('tickets').select('ticket_id,token_id,transaction_hash').limit(1).execute()
    print("✅ transaction_hash column EXISTS")
    print(f"Sample data: {result.data}")
except Exception as e:
    print(f"❌ transaction_hash column MISSING or ERROR:")
    print(f"   {e}")
    print("\nYou need to add this column to your Supabase tickets table:")
    print("ALTER TABLE tickets ADD COLUMN transaction_hash TEXT;")

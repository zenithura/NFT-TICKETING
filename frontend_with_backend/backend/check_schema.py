#!/usr/bin/env python3
"""Check if transaction_hash column exists in tickets table"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# Try to select with transaction_hash
try:
    result = supabase.table('tickets').select('ticket_id,token_id,transaction_hash').limit(1).execute()
    print("✅ transaction_hash column EXISTS")
    print(f"Sample data: {result.data}")
except Exception as e:
    print(f"❌ transaction_hash column MISSING or ERROR:")
    print(f"   {e}")
    print("\nYou need to add this column to your Supabase tickets table:")
    print("ALTER TABLE tickets ADD COLUMN transaction_hash TEXT;")

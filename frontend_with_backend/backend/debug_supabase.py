import os
from dotenv import load_dotenv
from supabase import create_client
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: '{url}'")
print(f"Key: '{key}'")

if not url or not key:
    print("Missing URL or Key")
    exit(1)

try:
    supabase = create_client(url, key)
    print("Client created")
    
    # Try a simple request
    # We don't know if 'events' table exists yet, but let's try
    # Or just check health if possible? Supabase-py doesn't have explicit health check
    # Let's try to select from a non-existent table or just 'events'
    print("Attempting request...")
    res = supabase.table('events').select("*").limit(1).execute()
    print("Request successful")
    print(res)
except Exception as e:
    print(f"Error: {e}")

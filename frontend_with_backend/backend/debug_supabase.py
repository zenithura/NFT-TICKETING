# File header: Supabase connection debugging script.
# Tests database connectivity and verifies environment configuration.

import os
from dotenv import load_dotenv
from supabase import create_client
import logging

# Purpose: Configure logging level for debugging output.
# Side effects: Sets logging configuration.
logging.basicConfig(level=logging.INFO)

# Purpose: Load environment variables from .env file.
# Side effects: Reads .env file, sets environment variables.
load_dotenv()

# Purpose: Retrieve Supabase connection credentials from environment.
# Side effects: Reads environment variables.
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Purpose: Display connection credentials for debugging (partial key shown).
# Side effects: Prints to console.
print(f"URL: '{url}'")
print(f"Key: '{key}'")

# Purpose: Validate that required environment variables are set.
# Side effects: Exits script if credentials missing.
if not url or not key:
    print("Missing URL or Key")
    exit(1)

# Purpose: Test Supabase client creation and database query.
# Side effects: Creates client, executes test query, prints results or error.
try:
    # Purpose: Initialize Supabase client connection.
    # Side effects: Creates database client instance.
    supabase = create_client(url, key)
    print("Client created")
    
    # Purpose: Test database connectivity by querying events table.
    # Side effects: Executes SELECT query, retrieves sample data.
    print("Attempting request...")
    res = supabase.table('events').select("*").limit(1).execute()
    print("Request successful")
    print(res)
except Exception as e:
    print(f"Error: {e}")

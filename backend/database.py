"""Database connection and Supabase client setup."""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Create Supabase client (for general use with anon key)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create admin client (for service operations with service key)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_supabase() -> Client:
    """Get Supabase client instance."""
    return supabase


def get_supabase_admin() -> Client:
    """Get Supabase admin client instance."""
    return supabase_admin

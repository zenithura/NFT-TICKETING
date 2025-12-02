import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

supabase_url = os.environ['SUPABASE_URL']
supabase_key = os.environ['SUPABASE_KEY']
supabase: Client = create_client(supabase_url, supabase_key)

def apply_migration():
    with open('add_blockchain_id.sql', 'r') as f:
        sql = f.read()
    
    # Supabase-py doesn't have a direct 'query' or 'execute_sql' method easily accessible for DDL 
    # unless we use the rpc or a specific function.
    # However, usually we can use the postgres connection directly if we have the connection string.
    # But here we only have URL and Key.
    # Let's try to use the 'rpc' if there is a 'exec_sql' function, or just use psycopg2 if available.
    
    # Checking requirements.txt might help.
    # If not, I might have to rely on the user or a pre-existing script.
    # 'create_tables.sql' exists. How was it run?
    # 'init_supabase_tables.sql' exists.
    
    # Let's check if psycopg2 is installed.
    try:
        import psycopg2
        # We need the connection string. usually postgres://postgres:[password]@[host]:[port]/postgres
        # The .env might have DB_URL.
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            cur.close()
            conn.close()
            print("Migration applied successfully via psycopg2")
            return
    except ImportError:
        print("psycopg2 not found")
    except Exception as e:
        print(f"psycopg2 failed: {e}")

    print("Could not apply migration automatically. Please run 'add_blockchain_id.sql' in your Supabase SQL editor.")

if __name__ == "__main__":
    apply_migration()

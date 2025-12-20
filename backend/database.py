"""Database connection and Supabase client setup."""
import os
import sqlite3
import json
from typing import Dict, Optional, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def is_placeholder(value: str) -> bool:
    """Check if a string is a placeholder value."""
    if not value:
        return True
    placeholders = ["your-project", "your-anon-key", "your-service-key", "example.com"]
    return any(p in value.lower() for p in placeholders)

class SQLiteSupabaseWrapper:
    """
    A wrapper that mimics the Supabase client API using SQLite.
    Supports basic table().select().execute() and table().insert().execute() patterns.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initialize SQLite database if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        # We'll run the schema initialization later via a separate call
        conn.close()

    def table(self, table_name: str):
        return SQLiteTableQuery(self.db_path, table_name)

class SQLiteTableQuery:
    def __init__(self, db_path: str, table_name: str):
        self.db_path = db_path
        self.table_name = table_name
        self.filters = []
        self.order_by = None
        self.limit_val = None
        self.offset_val = None

    def select(self, columns: str = "*"):
        self.columns = columns
        return self

    def eq(self, column: str, value: Any):
        self.filters.append((column, "=", value))
        return self

    def order(self, column: str, desc: bool = False):
        self.order_by = f"{column} {'DESC' if desc else 'ASC'}"
        return self

    def limit(self, value: int):
        self.limit_val = value
        return self

    def range(self, start: int, end: int):
        self.offset_val = start
        self.limit_val = end - start + 1
        return self

    def insert(self, data: Any):
        if isinstance(data, dict):
            data = [data]
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        results = []
        for item in data:
            columns = ", ".join(item.keys())
            placeholders = ", ".join(["?" for _ in item])
            values = list(item.values())
            
            # Convert dict/list to JSON for SQLite
            processed_values = []
            for v in values:
                if isinstance(v, (dict, list)):
                    processed_values.append(json.dumps(v))
                else:
                    processed_values.append(v)

            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, processed_values)
            
            # Fetch the inserted row
            last_id = cursor.lastrowid
            # Try to find the primary key column name (usually table_id or id)
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            pk_col = "id"
            for col in cursor.fetchall():
                if col['pk']:
                    pk_col = col['name']
                    break
            
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {pk_col} = ?", (last_id,))
            row = cursor.fetchone()
            if row:
                results.append(dict(row))
        
        conn.commit()
        conn.close()
        return SQLiteResponse(results)

    def execute(self):
        query = f"SELECT {self.columns} FROM {self.table_name}"
        params = []
        
        if self.filters:
            where_clauses = []
            for col, op, val in self.filters:
                where_clauses.append(f"{col} {op} ?")
                params.append(val)
            query += " WHERE " + " AND ".join(where_clauses)
        
        if self.order_by:
            query += f" ORDER BY {self.order_by}"
        
        if self.limit_val:
            query += f" LIMIT {self.limit_val}"
            if self.offset_val:
                query += f" OFFSET {self.offset_val}"

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            return SQLiteResponse(data)
        except sqlite3.OperationalError as e:
            print(f"SQLite Error: {e}")
            return SQLiteResponse([], error=str(e))
        finally:
            conn.close()

class SQLiteResponse:
    def __init__(self, data: List[Dict], error: Optional[str] = None):
        self.data = data
        self.error = error

# Check if we should use local database mode
USE_LOCAL_DB = is_placeholder(SUPABASE_URL) or is_placeholder(SUPABASE_KEY)
LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_database.db")

if USE_LOCAL_DB:
    print(f"🏠 Running in LOCAL DATABASE MODE (SQLite: {LOCAL_DB_PATH})")
    supabase = SQLiteSupabaseWrapper(LOCAL_DB_PATH)
    supabase_admin = supabase
else:
    # Create Supabase client (for general use with anon key)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Create admin client (for service operations with service key)
    supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_supabase() -> Any:
    """Get Supabase client instance (or SQLite wrapper)."""
    return supabase


def get_supabase_admin() -> Any:
    """Get Supabase admin client instance (or SQLite wrapper)."""
    return supabase_admin

def init_local_db():
    """Initialize the local SQLite database with schema."""
    if not USE_LOCAL_DB:
        return
    
    print("Initializing local database schema...")
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "complete_database_schema.sql")
    if not os.path.exists(schema_path):
        print(f"Error: Schema file not found at {schema_path}")
        return

    with open(schema_path, 'r') as f:
        sql = f.read()

    # Basic conversion from PostgreSQL to SQLite
    sql = sql.replace("BIGSERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    sql = sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    sql = sql.replace("TIMESTAMPTZ", "TIMESTAMP")
    sql = sql.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMP")
    sql = sql.replace("NOW()", "CURRENT_TIMESTAMP")
    sql = sql.replace("BOOLEAN DEFAULT FALSE", "INTEGER DEFAULT 0")
    sql = sql.replace("BOOLEAN DEFAULT TRUE", "INTEGER DEFAULT 1")
    sql = sql.replace("BOOLEAN NOT NULL DEFAULT FALSE", "INTEGER NOT NULL DEFAULT 0")
    sql = sql.replace("NUMERIC(18, 8)", "REAL")
    sql = sql.replace("NUMERIC(5, 2)", "REAL")
    sql = sql.replace("JSONB", "TEXT")
    sql = sql.replace("JSON", "TEXT")
    
    # Remove PostgreSQL specific parts
    import re
    # Remove DO blocks
    sql = re.sub(r"DO \$\$.*?END \$\$;", "", sql, flags=re.DOTALL)
    # Remove CREATE TYPE
    sql = re.sub(r"CREATE TYPE .*?;", "", sql, flags=re.DOTALL)
    # Remove RLS
    sql = re.sub(r"ALTER TABLE .*? ENABLE ROW LEVEL SECURITY;", "", sql)
    sql = re.sub(r"CREATE POLICY .*?;", "", sql)
    # Remove functions and triggers
    sql = re.sub(r"CREATE OR REPLACE FUNCTION .*? END; \$\$ language 'plpgsql';", "", sql, flags=re.DOTALL)
    sql = re.sub(r"CREATE TRIGGER .*?;", "", sql)
    sql = re.sub(r"DROP TRIGGER .*?;", "", sql)
    # Remove comments
    sql = re.sub(r"COMMENT ON .*?;", "", sql)
    
    # Split by semicolon and execute individually to skip errors
    statements = sql.split(';')
    
    conn = sqlite3.connect(LOCAL_DB_PATH)
    cursor = conn.cursor()
    success_count = 0
    error_count = 0
    
    for statement in statements:
        stmt = statement.strip()
        if not stmt or stmt.startswith('--'):
            continue
            
        try:
            cursor.execute(stmt)
            success_count += 1
        except sqlite3.Error as e:
            # Skip errors for things like "IF NOT EXISTS" which might not be perfectly handled
            # or other PG-specific syntax that slipped through
            if "already exists" not in str(e).lower():
                print(f"Skipping statement due to error: {e}\nStatement: {stmt[:100]}...")
                error_count += 1
    
    conn.commit()
    conn.close()
    print(f"✓ Local database schema initialization finished. Success: {success_count}, Errors skipped: {error_count}")

if __name__ == "__main__":
    init_local_db()

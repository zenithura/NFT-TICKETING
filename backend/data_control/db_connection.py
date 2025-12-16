"""Database connection utilities for Sprint 3 components."""
import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import redis
import yaml
from pathlib import Path
from typing import Optional

# Load configuration
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
config = {}
if config_path.exists():
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

# Database configuration (use environment variables directly)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'ticketing'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', 'change_me_in_prod'),
}

# Redis configuration (use environment variables directly)
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'password': os.getenv('REDIS_PASSWORD', None),
    'db': 0,
    'decode_responses': True
}

# Connection pool
_connection_pool: Optional[pool.ThreadedConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def get_db_pool():
    """Get or create database connection pool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                **DB_CONFIG
            )
        except Exception as e:
            print(f"Error creating connection pool: {e}")
            return None
    return _connection_pool


def get_db_connection():
    """Get a database connection from the pool."""
    pool = get_db_pool()
    if pool is None:
        return None
    try:
        conn = pool.getconn()
        return conn
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        return None


def return_db_connection(conn):
    """Return a connection to the pool."""
    pool = get_db_pool()
    if pool and conn:
        try:
            pool.putconn(conn)
        except Exception as e:
            print(f"Error returning connection to pool: {e}")


def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(**REDIS_CONFIG)
            # Test connection
            _redis_client.ping()
        except Exception as e:
            print(f"Error connecting to Redis: {e}")
            return None
    return _redis_client


def execute_query(query: str, params: tuple = None, fetch: bool = True):
    """Execute a database query and return results."""
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                if query.strip().upper().startswith('SELECT'):
                    return cur.fetchall()
                conn.commit()
                return cur.rowcount
            conn.commit()
            return None
    except Exception as e:
        conn.rollback()
        print(f"Error executing query: {e}")
        return None
    finally:
        return_db_connection(conn)


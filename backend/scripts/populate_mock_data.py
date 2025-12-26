import sqlite3
import random
import json
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_database.db")

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        print(e)
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    
    # Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_id INTEGER,
            total_amount REAL,
            status TEXT,
            created_at TIMESTAMP
        )
    ''')

    # Bot Detection Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_detection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            ip_address TEXT,
            risk_score REAL,
            detected_at TIMESTAMP
        )
    ''')

    # Security Alerts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attack_type TEXT,
            severity TEXT,
            description TEXT,
            status TEXT,
            created_at TIMESTAMP
        )
    ''')

    # Web Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS web_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT,
            method TEXT,
            status_code INTEGER,
            response_time_ms INTEGER,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    print("Tables created successfully.")

def populate_data():
    conn = create_connection()
    if conn is None:
        print("Error! cannot create the database connection.")
        return

    create_tables(conn)
    cursor = conn.cursor()
    
    print("Populating data...")

    # 1. Orders (Transactions)
    statuses = ['completed', 'pending', 'failed']
    now = datetime.now()
    
    for i in range(100):
        created_at = (now - timedelta(minutes=random.randint(0, 1440))).isoformat()
        total_amount = round(random.uniform(0.01, 2.0), 4)
        status = random.choices(statuses, weights=[80, 15, 5])[0]
        
        cursor.execute('''
            INSERT INTO orders (user_id, event_id, total_amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (random.randint(1, 50), random.randint(1, 10), total_amount, status, created_at))

    # 2. Bot Detection
    for i in range(50):
        detected_at = (now - timedelta(minutes=random.randint(0, 60))).isoformat()
        risk_score = round(random.random(), 2)
        
        cursor.execute('''
            INSERT INTO bot_detection (request_id, ip_address, risk_score, detected_at)
            VALUES (?, ?, ?, ?)
        ''', (f"req_{i}", f"192.168.1.{random.randint(1, 255)}", risk_score, detected_at))

    # 3. Security Alerts
    alert_types = ['SQL Injection', 'XSS Attempt', 'Brute Force', 'Abnormal Traffic']
    severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    for i in range(10):
        created_at = (now - timedelta(minutes=random.randint(0, 300))).isoformat()
        attack_type = random.choice(alert_types)
        severity = random.choice(severities)
        
        cursor.execute('''
            INSERT INTO security_alerts (attack_type, severity, description, created_at, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (attack_type, severity, f"Detected {attack_type} from IP", created_at, 'NEW'))

    # 4. Web Requests
    for i in range(200):
        created_at = (now - timedelta(minutes=random.randint(0, 60))).isoformat()
        response_time = random.randint(20, 500)
        status_code = random.choices([200, 201, 400, 404, 500], weights=[85, 10, 2, 2, 1])[0]
        
        cursor.execute('''
            INSERT INTO web_requests (endpoint, method, status_code, response_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', ('/api/tickets', 'GET', status_code, response_time, created_at))

    conn.commit()
    print("Data populated successfully!")
    conn.close()

if __name__ == '__main__':
    populate_data()

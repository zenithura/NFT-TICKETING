import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def generate_wallets(count=50):
    print(f"Generating {count} wallets...")
    wallets = []
    for _ in range(count):
        address = f"0x{uuid.uuid4().hex}"
        wallets.append({
            "address": address,
            "balance": round(random.uniform(0.1, 10.0), 4),
            "allowlist_status": random.choice([True, False]),
            "verification_level": random.randint(0, 3),
            "blacklisted": random.random() < 0.05
        })
    
    result = supabase.table("wallets").insert(wallets).execute()
    return result.data

def generate_users(wallets, count=50):
    print(f"Generating {count} users...")
    users = []
    roles = ['BUYER', 'ORGANIZER', 'ADMIN']
    for i in range(min(count, len(wallets))):
        wallet = wallets[i]
        username = f"user_{i}"
        users.append({
            "email": f"{username}@example.com",
            "password_hash": "hashed_password_placeholder", # In real app, use bcrypt
            "username": username,
            "first_name": f"First_{i}",
            "last_name": f"Last_{i}",
            "role": random.choices(roles, weights=[0.8, 0.15, 0.05])[0],
            "wallet_address": wallet["address"],
            "is_email_verified": True
        })
    
    result = supabase.table("users").insert(users).execute()
    return result.data

def generate_venues(count=5):
    print(f"Generating {count} venues...")
    venues = [
        {"name": "Crypto Arena", "location": "Los Angeles", "city": "LA", "country": "USA", "capacity": 20000},
        {"name": "Madison Square Garden", "location": "New York", "city": "NYC", "country": "USA", "capacity": 18000},
        {"name": "O2 Arena", "location": "London", "city": "London", "country": "UK", "capacity": 20000},
        {"name": "Wembley Stadium", "location": "London", "city": "London", "country": "UK", "capacity": 90000},
        {"name": "Allianz Arena", "location": "Munich", "city": "Munich", "country": "Germany", "capacity": 75000}
    ]
    
    result = supabase.table("venues").insert(venues[:count]).execute()
    return result.data

def generate_events(venues, count=10):
    print(f"Generating {count} events...")
    events = []
    event_names = ["NFT World Tour", "Blockchain Summit", "Crypto Concert", "Web3 Workshop", "Metaverse Meetup"]
    for i in range(count):
        venue = random.choice(venues)
        event_date = datetime.now(timezone.utc) + timedelta(days=random.randint(1, 60))
        events.append({
            "venue_id": venue["venue_id"],
            "name": f"{random.choice(event_names)} {i}",
            "description": "A premium NFT ticketing event.",
            "event_date": event_date.isoformat(),
            "start_time": "18:00:00",
            "end_time": "22:00:00",
            "total_supply": venue["capacity"],
            "available_tickets": venue["capacity"],
            "base_price": round(random.uniform(0.01, 0.1), 4),
            "status": "UPCOMING"
        })
    
    result = supabase.table("events").insert(events).execute()
    return result.data

def generate_tickets_and_orders(users, events, count=100):
    print(f"Generating {count} tickets and orders...")
    tickets = []
    for i in range(count):
        event = random.choice(events)
        user = random.choice(users)
        
        # Find wallet_id for the user
        wallet_response = supabase.table("wallets").select("wallet_id").eq("address", user["wallet_address"]).execute()
        wallet_id = wallet_response.data[0]["wallet_id"] if wallet_response.data else None
        
        if not wallet_id: continue

        token_id = f"TICK-{uuid.uuid4().hex[:8].upper()}"
        ticket_data = {
            "event_id": event["event_id"],
            "owner_wallet_id": wallet_id,
            "token_id": token_id,
            "tier": random.choice(['GENERAL', 'VIP', 'PREMIUM']),
            "purchase_price": event["base_price"],
            "status": "ACTIVE"
        }
        
        ticket_result = supabase.table("tickets").insert(ticket_data).execute()
        if ticket_result.data:
            ticket = ticket_result.data[0]
            order_data = {
                "buyer_wallet_id": wallet_id,
                "ticket_id": ticket["ticket_id"],
                "event_id": event["event_id"],
                "order_type": "PRIMARY",
                "price": ticket["purchase_price"],
                "total_amount": ticket["purchase_price"],
                "status": "COMPLETED",
                "transaction_hash": f"0x{uuid.uuid4().hex}"
            }
            supabase.table("orders").insert(order_data).execute()

def generate_security_alerts(users, count=30):
    print(f"Generating {count} security alerts...")
    alerts = []
    attack_types = ['XSS', 'SQL_INJECTION', 'BRUTE_FORCE', 'RATE_LIMIT_EXCEEDED']
    severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    for _ in range(count):
        user = random.choice(users)
        attack = random.choice(attack_types)
        alerts.append({
            "user_id": user["user_id"],
            "ip_address": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "attack_type": attack,
            "payload": f"Suspicious {attack} attempt",
            "endpoint": "/api/v1/tickets",
            "severity": random.choice(severities),
            "risk_score": random.randint(10, 100),
            "status": "NEW"
        })
    
    supabase.table("security_alerts").insert(alerts).execute()

def main():
    print("Starting synthetic data generation...")
    
    # 1. Wallets
    wallets = generate_wallets(50)
    
    # 2. Users
    users = generate_users(wallets, 50)
    
    # 3. Venues
    venues = generate_venues(5)
    
    # 4. Events
    events = generate_events(venues, 10)
    
    # 5. Tickets & Orders
    generate_tickets_and_orders(users, events, 100)
    
    # 6. Security Alerts
    generate_security_alerts(users, 30)
    
    print("Synthetic data generation complete! 🚀")

if __name__ == "__main__":
    main()

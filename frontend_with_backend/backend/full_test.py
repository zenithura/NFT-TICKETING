#!/usr/bin/env python3
"""Create a test event and mint a ticket"""
import requests

print("🎪 Creating Test Event and Minting Ticket\n")

# 1. Create a venue first
print("1️⃣ Creating venue...")
venue_response = requests.post(
    "http://localhost:5000/api/venues",
    json={
        "name": "Blockchain Test Arena",
        "location": "Test Location",
        "city": "Istanbul",
        "country": "Turkey",
        "capacity": 1000
    }
)
venue = venue_response.json()
print(f"   ✅ Venue created: {venue['name']} (ID: {venue['venue_id']})")

# 2. Create event
print("\n2️⃣ Creating event...")
event_response = requests.post(
    "http://localhost:5000/api/events",
    json={
        "venue_id": venue['venue_id'],
        "name": "Blockchain NFT Test Concert",
        "description": "Testing blockchain integration",
        "event_date": "2025-12-31T20:00:00Z",
        "total_supply": 50,
        "base_price": 0.1
    }
)
event = event_response.json()
print(f"   ✅ Event created: {event['name']}")
print(f"   Available: {event['available_tickets']}/{event['total_supply']}")
print(f"   Price: {event['base_price']} ETH")

# 3. Connect wallet
print("\n3️⃣ Connecting wallet...")
wallet_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
wallet_response = requests.post(
    "http://localhost:5000/api/wallet/connect",
    json={"address": wallet_address}
)
wallet = wallet_response.json()
print(f"   ✅ Wallet connected: {wallet_address[:10]}...")
print(f"   Balance: {wallet['balance']} ETH")

# 4. Mint ticket
print("\n4️⃣ Minting ticket on blockchain...")
mint_response = requests.post(
    "http://localhost:5000/api/tickets/mint",
    json={
        "event_id": event['event_id'],
        "buyer_address": wallet_address
    }
)

if mint_response.status_code == 200:
    ticket = mint_response.json()
    print(f"   ✅ SUCCESS! Ticket minted!")
    print(f"   Ticket ID (Database): {ticket['ticket_id']}")
    print(f"   Token ID (UUID): {ticket['token_id']}")
    
    if ticket.get('transaction_hash'):
        print(f"\n   🎉 BLOCKCHAIN TRANSACTION:")
        print(f"   TX Hash: {ticket['transaction_hash']}")
        print(f"\n   ✅ Ticket başarıyla blockchain'e mint edildi!")
    else:
        print(f"\n   ⚠️  Database'e kaydedildi ama blockchain TX yok")
else:
    print(f"   ❌ Error {mint_response.status_code}: {mint_response.text}")

print("\n" + "="*60)
print("Şimdi blockchain durumunu kontrol et:")
print("./venv/bin/python verify_blockchain.py")

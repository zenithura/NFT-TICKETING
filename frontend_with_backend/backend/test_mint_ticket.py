#!/usr/bin/env python3
"""Test ticket minting on blockchain"""
import requests
import json

print("🎫 Testing Ticket Purchase & Blockchain Minting\n")

# 1. Connect a test wallet
print("1️⃣ Connecting wallet...")
wallet_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"  # Second Hardhat account

response = requests.post(
    "http://localhost:5000/api/wallet/connect",
    json={"address": wallet_address}
)
print(f"   Status: {response.status_code}")
wallet = response.json()
print(f"   Wallet ID: {wallet.get('wallet_id')}")
print(f"   Balance: {wallet.get('balance')} ETH")

# 2. Get available events
print("\n2️⃣ Fetching events...")
response = requests.get("http://localhost:5000/api/events")
events = response.json()
if events:
    event = events[0]
    print(f"   Event: {event['name']}")
    print(f"   Available: {event['available_tickets']}/{event['total_supply']}")
    print(f"   Price: {event['base_price']} ETH")
else:
    print("   ❌ No events found!")
    exit(1)

# 3. Mint a ticket
print("\n3️⃣ Minting ticket...")
response = requests.post(
    "http://localhost:5000/api/tickets/mint",
    json={
        "event_id": event['event_id'],
        "buyer_address": wallet_address
    }
)

if response.status_code == 200:
    ticket = response.json()
    print(f"   ✅ Ticket minted!")
    print(f"   Ticket ID: {ticket.get('ticket_id')}")
    print(f"   Token ID: {ticket.get('token_id')}")
    print(f"   Transaction Hash: {ticket.get('transaction_hash')}")
    
    if ticket.get('transaction_hash'):
        print(f"\n   🎉 BLOCKCHAIN TRANSACTION SUCCESSFUL!")
        print(f"   TX: {ticket.get('transaction_hash')}")
    else:
        print(f"\n   ⚠️  Ticket created in DB but no blockchain TX")
else:
    print(f"   ❌ Error: {response.status_code}")
    print(f"   {response.text}")

print("\n" + "="*50)
print("Now run: ./venv/bin/python verify_blockchain.py")
print("to see the blockchain state updated!")

# File header: Test script for ticket minting on blockchain.
# Tests wallet connection, event retrieval, and ticket minting with blockchain verification.

#!/usr/bin/env python3
"""Test ticket minting on blockchain"""
import requests
import json

print("🎫 Testing Ticket Purchase & Blockchain Minting\n")

# Purpose: Connect test wallet to backend system.
# Side effects: Sends POST request, creates wallet record in database.
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

# Purpose: Retrieve available events from backend.
# Side effects: Sends GET request, retrieves event list from database.
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

# Purpose: Mint NFT ticket on blockchain for selected event.
# Side effects: Sends POST request, creates ticket record, executes blockchain transaction.
print("\n3️⃣ Minting ticket...")
response = requests.post(
    "http://localhost:5000/api/tickets/mint",
    json={
        "event_id": event['event_id'],
        "buyer_address": wallet_address
    }
)

# Purpose: Verify ticket minting success and display transaction details.
# Side effects: Prints ticket information and blockchain transaction hash.
if response.status_code == 200:
    ticket = response.json()
    print(f"   ✅ Ticket minted!")
    print(f"   Ticket ID: {ticket.get('ticket_id')}")
    print(f"   Token ID: {ticket.get('token_id')}")
    print(f"   Transaction Hash: {ticket.get('transaction_hash')}")
    
    # Purpose: Verify blockchain transaction was successful.
    # Side effects: Prints success message or warning.
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

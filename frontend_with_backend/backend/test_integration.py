import requests
import json
import os
import time

# Configuration
API_URL = "http://localhost:8000/api"

def test_mint_ticket():
    print("Testing mint ticket...")
    # 1. Create a wallet
    wallet_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8" # Hardhat Account #1
    
    # Connect wallet
    resp = requests.post(f"{API_URL}/wallet/connect", json={"address": wallet_address})
    if resp.status_code != 200:
        print(f"Failed to connect wallet: {resp.text}")
        return
    print("Wallet connected")
    
    # 2. Create venue
    venue_data = {
        "name": "Test Venue",
        "capacity": 100,
        "city": "Test City",
        "country": "Test Country"
    }
    resp = requests.post(f"{API_URL}/venues", json=venue_data)
    if resp.status_code != 200:
        print(f"Failed to create venue: {resp.text}")
        return
    venue_id = resp.json()['venue_id']
    print(f"Venue created: {venue_id}")
    
    # 3. Create event
    event_data = {
        "venue_id": venue_id,
        "name": "Test Event",
        "event_date": "2025-12-31",
        "total_supply": 10,
        "base_price": 10.0
    }
    resp = requests.post(f"{API_URL}/events", json=event_data)
    if resp.status_code != 200:
        print(f"Failed to create event: {resp.text}")
        return
    event_id = resp.json()['event_id']
    print(f"Event created: {event_id}")
    
    # 4. Mint ticket
    mint_data = {
        "event_id": event_id,
        "buyer_address": wallet_address
    }
    resp = requests.post(f"{API_URL}/tickets/mint", json=mint_data)
    if resp.status_code != 200:
        print(f"Failed to mint ticket: {resp.text}")
        return
        
    ticket = resp.json()
    print(f"Ticket minted: {ticket}")
    
    if 'transaction_hash' in ticket and ticket['transaction_hash']:
        print(f"Transaction Hash: {ticket['transaction_hash']}")
    else:
        print("WARNING: No transaction hash returned!")

if __name__ == "__main__":
    # Wait for server to start if running in parallel
    time.sleep(2)
    try:
        test_mint_ticket()
    except Exception as e:
        print(f"Test failed: {e}")

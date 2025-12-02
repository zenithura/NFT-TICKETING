# File header: Integration test script for ticket minting workflow.
# Tests complete flow: wallet connection, venue creation, event creation, and ticket minting.

import requests
import json
import os
import time

# Purpose: API base URL for backend server.
# Side effects: None - configuration constant.
API_URL = "http://localhost:8000/api"

# Purpose: Test complete ticket minting workflow end-to-end.
# Side effects: Makes HTTP requests to API, prints test results.
def test_mint_ticket():
    print("Testing mint ticket...")
    # Purpose: Use Hardhat test account #1 for testing.
    # Side effects: Sets wallet address for test.
    wallet_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8" # Hardhat Account #1
    
    # Purpose: Connect wallet to backend system.
    # Side effects: Sends POST request, creates wallet record in database.
    resp = requests.post(f"{API_URL}/wallet/connect", json={"address": wallet_address})
    if resp.status_code != 200:
        print(f"Failed to connect wallet: {resp.text}")
        return
    print("Wallet connected")
    
    # Purpose: Create test venue for event.
    # Side effects: Sends POST request, creates venue record in database.
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
    
    # Purpose: Create test event linked to venue.
    # Side effects: Sends POST request, creates event record in database.
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
    
    # Purpose: Mint NFT ticket on blockchain for the event.
    # Side effects: Sends POST request, creates ticket record, executes blockchain transaction.
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
    
    # Purpose: Verify blockchain transaction hash was returned.
    # Side effects: Prints transaction hash or warning message.
    if 'transaction_hash' in ticket and ticket['transaction_hash']:
        print(f"Transaction Hash: {ticket['transaction_hash']}")
    else:
        print("WARNING: No transaction hash returned!")

# Purpose: Main execution block - run integration test with delay for server startup.
# Side effects: Waits 2 seconds, executes test, handles exceptions.
if __name__ == "__main__":
    # Purpose: Wait for server to start if running in parallel.
    # Side effects: Delays execution by 2 seconds.
    time.sleep(2)
    try:
        test_mint_ticket()
    except Exception as e:
        print(f"Test failed: {e}")

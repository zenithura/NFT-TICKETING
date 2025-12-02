import requests
import json
import time

BASE_URL = "http://localhost:8000"
TEST_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

def debug_resell():
    
    # Fetch Server Address
    print("Fetching Server Address...")
    try:
        res = requests.get(f"{BASE_URL}/tickets/server-address")
        if res.status_code == 200 and res.json().get("address"):
            global TEST_ADDRESS
            TEST_ADDRESS = res.json()["address"]
            print(f"Using Server Address: {TEST_ADDRESS}")
        else:
            print("Could not fetch server address, using default.")
    except Exception as e:
        print(f"Error fetching server address: {e}")

    print(f"Debugging Resell Flow for {TEST_ADDRESS}")
    
    # 0. Ensure User Exists
    print("0. Connecting User...")
    auth_payload = {"address": TEST_ADDRESS}
    res = requests.post(f"{BASE_URL}/auth/connect", json=auth_payload)
    print(f"Auth Status: {res.status_code}")

    # 1. Mint Ticket
    print("1. Minting Ticket...")
    # Use a unique event ID or ensure it exists. 
    # Ideally we should create an event first, but let's assume event_id 1 exists or we use the one from previous tests.
    # Let's use event_id 2 which we used in verify_endpoints.py
    mint_payload = {
        "to_address": TEST_ADDRESS,
        "token_uri": "ipfs://debug_resell",
        "event_id": 4,
        "price": 0.01
    }
    res = requests.post(f"{BASE_URL}/tickets/mint", json=mint_payload)
    print(f"Mint Status: {res.status_code}")
    if res.status_code != 200:
        print(f"Mint Error: {res.text}")
        return
    
    # We don't get the ticket ID back from mint endpoint (it returns tx receipt).
    # So we need to fetch user tickets to find the latest one.
    print("2. Fetching User Tickets...")
    time.sleep(2) # Wait for DB sync?
    res = requests.get(f"{BASE_URL}/tickets/user/{TEST_ADDRESS}")
    print(f"Get Tickets Status: {res.status_code}")
    tickets = res.json()
    if not tickets:
        print("No tickets found for user. DB Sync failed?")
        return
    
    # Get the last ticket
    latest_ticket = tickets[-1]
    ticket_id = latest_ticket['id']
    print(f"Found Ticket ID: {ticket_id}")
    
    # 2.5 Approve Marketplace
    print("2.5. Approving Marketplace...")
    res = requests.post(f"{BASE_URL}/tickets/approve-marketplace")
    print(f"Approve Status: {res.status_code}")
    if res.status_code != 200:
        print(f"Approve Error: {res.text}")
        return

    # 3. List Ticket
    print(f"3. Listing Ticket {ticket_id}...")
    list_payload = {
        "ticket_id": ticket_id,
        "price": 0.02
    }
    res = requests.post(f"{BASE_URL}/marketplace/list", json=list_payload)
    print(f"List Status: {res.status_code}")
    print(f"List Response: {res.text}")
    if res.status_code != 200:
        print(f"List Error: {res.text}")
        return
        
    # 4. Verify Listing in DB
    print("4. Verifying Listing in DB...")
    time.sleep(2)
    res = requests.get(f"{BASE_URL}/marketplace/?status=active")
    listings = res.json()
    found = False
    for listing in listings:
        if listing['ticket_id'] == ticket_id:
            print(f"Found Listing: {listing}")
            found = True
            break
            
    if not found:
        print("Listing NOT found in DB!")
    else:
        print("Listing verified in DB.")

if __name__ == "__main__":
    debug_resell()

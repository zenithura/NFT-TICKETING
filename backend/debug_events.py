import requests
import json

BASE_URL = "http://localhost:8000"
TEST_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e" # Use the address from verify_endpoints.py

def debug_event_creation():
    print(f"Debugging Event Creation for {TEST_ADDRESS}")
    
    # 1. Ensure user exists
    print("1. Connecting User...")
    auth_payload = {"address": TEST_ADDRESS}
    res = requests.post(f"{BASE_URL}/auth/connect", json=auth_payload)
    print(f"Auth Status: {res.status_code}")
    if res.status_code != 200:
        print(f"Auth Error: {res.text}")
        return

    # 2. Check Role / Upgrade
    print("2. Upgrading to Organizer...")
    res = requests.post(f"{BASE_URL}/auth/upgrade-to-organizer/{TEST_ADDRESS}")
    print(f"Upgrade Status: {res.status_code}")
    # It might return 200 or 400 if already organizer, or 404.
    # Let's assume it works or is already organizer.

    # 3. Create Event
    print("3. Creating Event...")
    event_payload = {
        "name": "Debug Event",
        "description": "Testing event creation",
        "date": "2025-12-31T20:00:00",
        "location": "Metaverse",
        "total_tickets": 100,
        "price": 0.1,
        "organizer_address": TEST_ADDRESS,
        "image_url": "https://example.com/image.png",
        "category": "Music",
        "currency": "ETH"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/events/", json=event_payload)
        print(f"Create Event Status: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    debug_event_creation()

import requests
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None):
    url = f"{BASE_URL}{path}"
    print(f"Testing {method} {url}...")
    try:
        if method == "POST":
            res = requests.post(url, json=data)
        else:
            res = requests.get(url)
        
        print(f"Status: {res.status_code}")
        # print(f"Response: {res.text}")
        return res.status_code
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    # Test Mint
    mint_data = {
        "to_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "token_uri": "ipfs://test",
        "event_id": 2, # Use a new event ID to avoid conflicts or ensure it exists
        "price": 0.01
    }
    test_endpoint("POST", "/tickets/mint", mint_data)

    # Test List
    list_data = {
        "ticket_id": 1,
        "price": 0.001
    }
    test_endpoint("POST", "/marketplace/list", list_data)

    # Test Buy
    buy_data = {
        "ticket_id": 1,
        "value": 0.001
    }
    test_endpoint("POST", "/marketplace/buy", buy_data)

if __name__ == "__main__":
    main()

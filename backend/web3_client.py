import json
import os
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
print(f"Loading .env from {env_path}")
load_dotenv(env_path, override=True)

# Configuration
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

print(f"Web3 Client Loaded. RPC: {SEPOLIA_RPC_URL is not None}, Key: {PRIVATE_KEY is not None and len(PRIVATE_KEY) > 0}")
DEPLOYMENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "deployments", "sepolia.json")

if not SEPOLIA_RPC_URL:
    print("Warning: SEPOLIA_RPC_URL not set in .env")

if not PRIVATE_KEY:
    print("Warning: PRIVATE_KEY not set in .env")

# Web3 Setup
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
if PRIVATE_KEY:
    account = w3.eth.account.from_key(PRIVATE_KEY)
else:
    account = None

# Load Contracts
contracts: Dict[str, Any] = {}

def load_contracts():
    global contracts
    try:
        if not os.path.exists(DEPLOYMENTS_FILE):
            print(f"Deployments file not found at {DEPLOYMENTS_FILE}")
            return

        with open(DEPLOYMENTS_FILE, "r") as f:
            data = json.load(f)
            
        # Handle nested structure if present, or flat structure
        # The user's example showed data.get("contracts", data)
        contract_data = data.get("contracts", data)
            
        for name, info in contract_data.items():
            contracts[name] = w3.eth.contract(
                address=info["address"],
                abi=info["abi"]
            )
        print(f"Loaded contracts: {list(contracts.keys())}")
    except Exception as e:
        print(f"Error loading contracts: {e}")

# Initialize contracts on module load (or call explicitly)
load_contracts()

def send_transaction(func, value=0):
    """
    Helper to send a transaction using the server's private key.
    """
    if not account:
        raise Exception("Server wallet not configured (missing PRIVATE_KEY)")

    try:
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Estimate gas? Or use fixed. User used fixed 2000000.
        # Let's try to estimate or use a safe default.
        tx_params = {
            'chainId': 11155111, # Sepolia
            'gas': 2000000, # Safe default from user code
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'value': w3.to_wei(value, 'ether'),
            'from': account.address
        }
        
        tx = func.build_transaction(tx_params)
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {"tx_hash": tx_hash.hex(), "status": receipt.status}
    except Exception as e:
        print(f"Transaction Error: {e}")
        raise e

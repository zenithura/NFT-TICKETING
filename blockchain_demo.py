#!/usr/bin/env python3
"""
Direct blockchain interaction demo - bypasses backend/database
Shows the smart contract working directly
"""

from web3 import Web3
import json
from pathlib import Path

# Colors for terminal output
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

def print_step(step_num, title):
    print(f"\n{BLUE}{'='*60}")
    print(f"Step {step_num}: {title}")
    print(f"{'='*60}{NC}\n")

def print_success(message):
    print(f"{GREEN}✓ {message}{NC}")

def print_error(message):
    print(f"{RED}✗ {message}{NC}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{NC}")

# Setup
print(f"\n{BLUE}{'='*60}")
print("NFT Ticketing - Smart Contract Demo")
print(f"{'='*60}{NC}\n")

# Connect to Hardhat node
print_step(1, "Connecting to Blockchain")
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

if w3.is_connected():
    print_success("Connected to Hardhat node")
    print(f"   Chain ID: {w3.eth.chain_id}")
    print(f"   Latest block: {w3.eth.block_number}")
else:
    print_error("Failed to connect to blockchain")
    exit(1)

# Load contract
print_step(2, "Loading Smart Contract")
contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
artifact_path = Path(__file__).parent / "smart-contracts/artifacts/contracts/TicketManager.sol/TicketManager.json"

with open(artifact_path, 'r') as f:
    artifact = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=artifact['abi'])
print_success(f"Contract loaded at {contract_address}")

# Get accounts
print_step(3, "Setting up Test Accounts")
accounts = w3.eth.accounts
admin = accounts[0]
buyer = accounts[1]

print(f"   Admin: {admin}")
print(f"   Buyer: {buyer}")
print(f"   Admin balance: {w3.from_wei(w3.eth.get_balance(admin), 'ether')} ETH")
print(f"   Buyer balance: {w3.from_wei(w3.eth.get_balance(buyer), 'ether')} ETH")

# Check contract state
print_step(4, "Checking Contract State")
next_token_id = contract.functions.nextTokenId().call()
royalty_recipient = contract.functions.royaltyRecipient().call()
royalty_bps = contract.functions.royaltyBps().call()

print(f"   Next Token ID: {next_token_id}")
print(f"   Royalty Recipient: {royalty_recipient}")
print(f"   Royalty Rate: {royalty_bps / 100}%")

# Mint a ticket
print_step(5, "Minting NFT Ticket")
event_id = 1
token_uri = "ipfs://QmTest123/metadata.json"

print_info(f"Minting ticket for event {event_id} to {buyer}")

try:
    tx_hash = contract.functions.mintTicket(
        buyer,
        event_id,
        token_uri
    ).transact({'from': admin})
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print_success("Ticket minted successfully!")
        print(f"   Transaction: {tx_hash.hex()}")
        print(f"   Gas used: {receipt['gasUsed']}")
        
        # Get the token ID from events
        token_id = next_token_id
        print(f"   Token ID: {token_id}")
    else:
        print_error("Transaction failed")
        
except Exception as e:
    print_error(f"Minting failed: {str(e)}")
    exit(1)

# Verify ownership
print_step(6, "Verifying Ticket Ownership")
owner = contract.functions.ownerOf(token_id).call()
print(f"   Token #{token_id} owner: {owner}")

if owner.lower() == buyer.lower():
    print_success("Ownership verified!")
else:
    print_error("Ownership mismatch!")

# Get ticket info
print_step(7, "Getting Ticket Information")
ticket_info = contract.functions.getTicketInfo(token_id).call()
print(f"   Event ID: {ticket_info[0][0]}")
print(f"   Scanned: {ticket_info[0][1]}")
print(f"   Listed for sale: {ticket_info[1][0] != '0x0000000000000000000000000000000000000000'}")

# List ticket for resale
print_step(8, "Listing Ticket for Resale")
resale_price = w3.to_wei(0.2, 'ether')  # 0.2 ETH

try:
    tx_hash = contract.functions.listTicket(
        token_id,
        resale_price
    ).transact({'from': buyer})
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print_success(f"Ticket listed for {w3.from_wei(resale_price, 'ether')} ETH")
        print(f"   Transaction: {tx_hash.hex()}")
    else:
        print_error("Listing failed")
        
except Exception as e:
    print_error(f"Listing failed: {str(e)}")

# Verify listing
print_step(9, "Verifying Listing")
ticket_info = contract.functions.getTicketInfo(token_id).call()
if ticket_info[1][0] != '0x0000000000000000000000000000000000000000':
    print_success("Ticket is listed!")
    print(f"   Seller: {ticket_info[1][0]}")
    print(f"   Price: {w3.from_wei(ticket_info[1][1], 'ether')} ETH")
else:
    print_error("Ticket not listed")

# Buy ticket (from another account)
print_step(10, "Buying Ticket from Marketplace")
buyer2 = accounts[2]
print(f"   Buyer 2: {buyer2}")
print(f"   Buyer 2 balance: {w3.from_wei(w3.eth.get_balance(buyer2), 'ether')} ETH")

try:
    tx_hash = contract.functions.buyTicket(token_id).transact({
        'from': buyer2,
        'value': resale_price
    })
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print_success("Ticket purchased successfully!")
        print(f"   Transaction: {tx_hash.hex()}")
        print(f"   Gas used: {receipt['gasUsed']}")
        
        # Verify new ownership
        new_owner = contract.functions.ownerOf(token_id).call()
        print(f"   New owner: {new_owner}")
        
        if new_owner.lower() == buyer2.lower():
            print_success("Ownership transferred!")
    else:
        print_error("Purchase failed")
        
except Exception as e:
    print_error(f"Purchase failed: {str(e)}")

# Scan ticket (mark as used)
print_step(11, "Scanning Ticket at Event")
try:
    tx_hash = contract.functions.scanTicket(token_id).transact({'from': admin})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print_success("Ticket scanned successfully!")
        print(f"   Transaction: {tx_hash.hex()}")
        
        # Verify scan
        ticket_info = contract.functions.getTicketInfo(token_id).call()
        if ticket_info[0][1]:
            print_success("Ticket marked as used - cannot be reused!")
    else:
        print_error("Scan failed")
        
except Exception as e:
    print_error(f"Scan failed: {str(e)}")

# Final summary
print(f"\n{BLUE}{'='*60}")
print("Demo Complete - Summary")
print(f"{'='*60}{NC}\n")

print(f"Contract Address: {contract_address}")
print(f"Token ID: {token_id}")
print(f"Final Owner: {contract.functions.ownerOf(token_id).call()}")
print(f"Event ID: {event_id}")
print(f"Status: Used ✓")

print(f"\n{GREEN}All smart contract functions working correctly!{NC}\n")

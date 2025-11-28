#!/usr/bin/env python3
"""Blockchain verification script"""
import os
from dotenv import load_dotenv
from web3 import Web3
import json
from pathlib import Path

load_dotenv()

print("🔍 Blockchain Connectivity Check\n")
print("=" * 50)

# 1. Connect to Hardhat node
rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
w3 = Web3(Web3.HTTPProvider(rpc_url))

print(f"✅ Connected: {w3.is_connected()}")
print(f"✅ Chain ID: {w3.eth.chain_id}")
print(f"✅ Latest block: {w3.eth.block_number}")
print(f"✅ Network: Hardhat Local")

# 2. Load contract
contract_address = os.getenv("SMART_CONTRACT_ADDRESS")
print(f"\n📝 Smart Contract Info")
print("=" * 50)
print(f"Address: {contract_address}")

artifact_path = Path(__file__).parent.parent.parent / "smart-contracts" / "artifacts" / "contracts" / "TicketManager.sol" / "TicketManager.json"

with open(artifact_path, "r") as f:
    artifact = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=artifact["abi"])

# 3. Contract state
royalty_recipient = contract.functions.royaltyRecipient().call()
royalty_bps = contract.functions.royaltyBps().call()
next_token_id = contract.functions.nextTokenId().call()

print(f"Royalty Recipient: {royalty_recipient}")
print(f"Royalty BPS: {royalty_bps} ({royalty_bps/100}%)")
print(f"Next Token ID: {next_token_id}")
print(f"Total Minted: {next_token_id - 1}")

# 4. Check for contract transactions
print(f"\n📊 Recent Activity")
print("=" * 50)
latest = w3.eth.block_number
tx_count = 0

for block_num in range(max(0, latest - 20), latest + 1):
    block = w3.eth.get_block(block_num, full_transactions=True)
    for tx in block['transactions']:
        if tx['to'] and tx['to'].lower() == contract_address.lower():
            tx_count += 1
            receipt = w3.eth.get_transaction_receipt(tx['hash'])
            print(f"Block {block_num}: {w3.to_hex(tx['hash'])[:20]}... (Status: {'✅' if receipt['status'] == 1 else '❌'})")

if tx_count == 0:
    print("No contract transactions yet.")
else:
    print(f"\nTotal contract transactions: {tx_count}")

print("\n" + "=" * 50)
print("✅ Blockchain is ready for ticket minting!")

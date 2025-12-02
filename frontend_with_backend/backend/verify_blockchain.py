# File header: Blockchain connectivity and contract verification script.
# Tests Web3 connection, loads TicketManager contract, and displays contract state and recent activity.

#!/usr/bin/env python3
"""Blockchain verification script"""
import os
from dotenv import load_dotenv
from web3 import Web3
import json
from pathlib import Path

# Purpose: Load environment variables from .env file.
# Side effects: Reads .env file, sets environment variables.
load_dotenv()

print("🔍 Blockchain Connectivity Check\n")
print("=" * 50)

# Purpose: Connect to local Hardhat blockchain node.
# Side effects: Creates Web3 HTTP provider connection.
rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Purpose: Display blockchain connection status and network information.
# Side effects: Prints connection details to console.
print(f"✅ Connected: {w3.is_connected()}")
print(f"✅ Chain ID: {w3.eth.chain_id}")
print(f"✅ Latest block: {w3.eth.block_number}")
print(f"✅ Network: Hardhat Local")

# Purpose: Load TicketManager smart contract ABI and create contract instance.
# Side effects: Reads contract artifact JSON, creates Web3 contract instance.
contract_address = os.getenv("SMART_CONTRACT_ADDRESS")
print(f"\n📝 Smart Contract Info")
print("=" * 50)
print(f"Address: {contract_address}")

# Purpose: Construct path to compiled contract artifact.
# Side effects: Builds file path from project structure.
artifact_path = Path(__file__).parent.parent.parent / "smart-contracts" / "artifacts" / "contracts" / "TicketManager.sol" / "TicketManager.json"

# Purpose: Load contract ABI from artifact file.
# Side effects: Reads JSON file, parses contract ABI.
with open(artifact_path, "r") as f:
    artifact = json.load(f)

# Purpose: Create Web3 contract instance for interaction.
# Side effects: Initializes contract with address and ABI.
contract = w3.eth.contract(address=contract_address, abi=artifact["abi"])

# Purpose: Query contract state variables (royalty settings and token counter).
# Side effects: Executes read-only contract calls.
royalty_recipient = contract.functions.royaltyRecipient().call()
royalty_bps = contract.functions.royaltyBps().call()
next_token_id = contract.functions.nextTokenId().call()

# Purpose: Display contract configuration and minting statistics.
# Side effects: Prints contract state to console.
print(f"Royalty Recipient: {royalty_recipient}")
print(f"Royalty BPS: {royalty_bps} ({royalty_bps/100}%)")
print(f"Next Token ID: {next_token_id}")
print(f"Total Minted: {next_token_id - 1}")

# Purpose: Scan recent blocks for transactions to the contract address.
# Side effects: Iterates through blocks, retrieves transaction receipts.
print(f"\n📊 Recent Activity")
print("=" * 50)
latest = w3.eth.block_number
tx_count = 0

# Purpose: Check last 20 blocks for contract transactions.
# Side effects: Retrieves block data, filters transactions, displays results.
for block_num in range(max(0, latest - 20), latest + 1):
    block = w3.eth.get_block(block_num, full_transactions=True)
    for tx in block['transactions']:
        if tx['to'] and tx['to'].lower() == contract_address.lower():
            tx_count += 1
            receipt = w3.eth.get_transaction_receipt(tx['hash'])
            print(f"Block {block_num}: {w3.to_hex(tx['hash'])[:20]}... (Status: {'✅' if receipt['status'] == 1 else '❌'})")

# Purpose: Display transaction count summary.
# Side effects: Prints summary message.
if tx_count == 0:
    print("No contract transactions yet.")
else:
    print(f"\nTotal contract transactions: {tx_count}")

print("\n" + "=" * 50)
print("✅ Blockchain is ready for ticket minting!")

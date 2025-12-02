# File header: Blockchain service wrapper for interacting with TicketManager smart contract.
# Handles Web3 connections, contract loading, and transaction execution for ticket minting and scanning.

import json
import os
from pathlib import Path
from web3 import Web3
import logging

logger = logging.getLogger(__name__)

# Purpose: Service class for blockchain interactions with TicketManager contract.
# Handles connection, contract loading, and transaction building.
class BlockchainService:
    # Purpose: Initialize blockchain connection and load smart contract.
    # Side effects: Connects to RPC endpoint, loads contract ABI, reads environment variables.
    def __init__(self):
        self.rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        self.contract_address = os.getenv("SMART_CONTRACT_ADDRESS")
        self.private_key = os.getenv("SERVER_WALLET_PRIVATE_KEY")
        self.wallet_address = os.getenv("SERVER_WALLET_ADDRESS")
        
        if not self.w3.is_connected():
            logger.error("Failed to connect to blockchain")
            raise Exception("Failed to connect to blockchain")
            
        logger.info(f"Connected to blockchain at {self.rpc_url}")
        
        self.contract = self._load_contract()

    # Purpose: Load smart contract ABI from compiled artifacts and create contract instance.
    # Returns: Web3 contract instance or None if address not configured.
    # Side effects: Reads JSON file from filesystem.
    def _load_contract(self):
        # Path to artifacts
        # Assuming backend is at frontend_with_backend/backend
        # and artifacts are at smart-contracts/artifacts
        base_dir = Path(__file__).parent.parent.parent
        artifact_path = base_dir / "smart-contracts" / "artifacts" / "contracts" / "TicketManager.sol" / "TicketManager.json"
        
        if not artifact_path.exists():
            logger.error(f"Artifact not found at {artifact_path}")
            raise FileNotFoundError(f"Artifact not found at {artifact_path}")
            
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
            
        if not self.contract_address:
            logger.warning("SMART_CONTRACT_ADDRESS not set")
            return None
            
        return self.w3.eth.contract(address=self.contract_address, abi=artifact["abi"])

    # Purpose: Mint a new NFT ticket on the blockchain.
    # Params: to_address (str) — recipient wallet address; event_id (int) — event identifier; token_uri (str) — metadata URI.
    # Returns: Transaction hash string or None if contract/key not configured.
    # Side effects: Sends signed transaction to blockchain, waits for confirmation.
    def mint_ticket(self, to_address: str, event_id: int, token_uri: str):
        if not self.contract or not self.private_key:
            logger.error("Contract or private key not configured")
            return None

        try:
            nonce = self.w3.eth.get_transaction_count(self.wallet_address)
            
            # Purpose: Build transaction to call mintTicket function on contract.
            # Side effects: Creates transaction object with gas and nonce.
            tx = self.contract.functions.mintTicket(
                to_address,
                event_id,
                token_uri
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 2000000, # Hardcoded gas limit for dev
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Purpose: Sign transaction with server's private key.
            # Side effects: Creates signed transaction bytes.
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            # Purpose: Broadcast signed transaction to blockchain network.
            # Side effects: Sends transaction to blockchain.
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Purpose: Wait for transaction to be mined and confirmed.
            # Side effects: Blocks until transaction receipt is available.
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Parse logs to get tokenId
            # TicketMinted(uint256 indexed tokenId, address indexed to, uint256 indexed eventId)
            # We can find the event in logs
            
            # Simple way: return tx hash and let caller handle it, or parse here.
            # Let's try to parse tokenId
            
            # For now just return tx hash
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            logger.error(f"Error minting ticket on chain: {e}")
            raise e

    # Purpose: Mark a ticket as scanned on the blockchain to prevent reuse.
    # Params: token_id (int) — NFT token identifier.
    # Returns: Transaction hash string or None if contract/key not configured.
    # Side effects: Sends signed transaction to blockchain, waits for confirmation.
    def scan_ticket(self, token_id: int):
        if not self.contract or not self.private_key:
            logger.error("Contract or private key not configured")
            return None
            
        try:
            nonce = self.w3.eth.get_transaction_count(self.wallet_address)
            
            # Purpose: Build transaction to call scanTicket function on contract.
            # Side effects: Creates transaction object with gas and nonce.
            tx = self.contract.functions.scanTicket(token_id).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Purpose: Sign and broadcast transaction to mark ticket as scanned.
            # Side effects: Sends transaction to blockchain, waits for confirmation.
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            logger.error(f"Error scanning ticket on chain: {e}")
            raise e

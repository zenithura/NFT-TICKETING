// File header: Web3 service class for interacting with TicketManager smart contract.
// Handles wallet connection, contract interactions, and ticket operations via ethers.js.

import { ethers } from 'ethers';

// Purpose: Import compiled contract ABI from Hardhat artifacts.
// Side effects: None - static import.
import TicketManagerArtifact from '../../../smart-contracts/artifacts/contracts/TicketManager.sol/TicketManager.json';

// Purpose: Contract address from environment or default localhost deployment address.
// Side effects: None - constant configuration.
const CONTRACT_ADDRESS = process.env.REACT_APP_CONTRACT_ADDRESS || '0x5FbDB2315678afecb367f032d93F642f64180aa3';
// Purpose: Blockchain RPC endpoint URL from environment or default localhost.
const RPC_URL = process.env.REACT_APP_RPC_URL || 'http://127.0.0.1:8545';

// Purpose: Service class for Web3 blockchain interactions with TicketManager contract.
// Manages provider, signer, contract instance, and account state.
class Web3Service {
    // Purpose: Initialize service with null provider, signer, contract, and account.
    // Side effects: None - initializes instance variables.
    constructor() {
        this.provider = null;
        this.signer = null;
        this.contract = null;
        this.account = null;
    }

    // Purpose: Connect to MetaMask or other Web3 wallet provider.
    // Returns: Promise resolving to connected account address.
    // Side effects: Requests account access, creates provider/signer, initializes contract instance.
    async connectWallet() {
        if (typeof window.ethereum !== 'undefined') {
            try {
                // Request account access
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });

                // Create provider and signer
                this.provider = new ethers.BrowserProvider(window.ethereum);
                this.signer = await this.provider.getSigner();
                this.account = accounts[0];

                // Initialize contract
                this.contract = new ethers.Contract(
                    CONTRACT_ADDRESS,
                    TicketManagerArtifact.abi,
                    this.signer
                );

                return this.account;
            } catch (error) {
                console.error('Error connecting wallet:', error);
                throw error;
            }
        } else {
            throw new Error('Please install MetaMask or another Web3 wallet');
        }
    }

    // Purpose: Get read-only provider for querying contract without wallet connection.
    // Returns: ethers provider instance.
    // Side effects: Creates provider and contract instance if not already initialized.
    getReadOnlyProvider() {
        if (!this.provider) {
            this.provider = new ethers.JsonRpcProvider(RPC_URL);
            this.contract = new ethers.Contract(
                CONTRACT_ADDRESS,
                TicketManagerArtifact.abi,
                this.provider
            );
        }
        return this.provider;
    }

    // Purpose: Retrieve all tickets owned by a specific wallet address.
    // Params: address (string) — Ethereum wallet address to query.
    // Returns: Promise resolving to array of ticket objects with token ID, event ID, scan status, and listing info.
    // Side effects: Queries blockchain events, makes multiple contract calls.
    async getOwnedTickets(address) {
        if (!this.contract) {
            this.getReadOnlyProvider();
        }

        // Purpose: Query Transfer events to find all tickets transferred to the address.
        // Side effects: Queries blockchain event logs.
        const filter = this.contract.filters.Transfer(null, address);
        const events = await this.contract.queryFilter(filter);

        const tokenIds = events.map(event => event.args.tokenId);

        // Purpose: Get ticket information for each token ID and verify current ownership.
        // Side effects: Makes contract calls for each token, filters out burned/transferred tokens.
        const tickets = await Promise.all(
            tokenIds.map(async (tokenId) => {
                try {
                    const owner = await this.contract.ownerOf(tokenId);
                    if (owner.toLowerCase() === address.toLowerCase()) {
                        const info = await this.contract.getTicketInfo(tokenId);
                        return {
                            tokenId: tokenId.toString(),
                            eventId: info.info.eventId.toString(),
                            scanned: info.info.scanned,
                            listing: info.listing.seller !== ethers.ZeroAddress ? {
                                seller: info.listing.seller,
                                price: ethers.formatEther(info.listing.price)
                            } : null
                        };
                    }
                } catch (error) {
                    // Purpose: Handle tokens that may have been burned or transferred.
                    return null;
                }
            })
        );

        return tickets.filter(t => t !== null);
    }

    // Purpose: List a ticket for resale on the marketplace.
    // Params: tokenId (number/string) — ticket token ID; priceInEth (string/number) — listing price in ETH.
    // Returns: Promise resolving to transaction receipt.
    // Side effects: Sends transaction to blockchain, requires wallet connection.
    async listTicket(tokenId, priceInEth) {
        if (!this.contract || !this.signer) {
            throw new Error('Wallet not connected');
        }

        const priceInWei = ethers.parseEther(priceInEth.toString());
        const tx = await this.contract.listTicket(tokenId, priceInWei);
        await tx.wait();
        return tx.hash;
    }

    // Cancel a listing
    async cancelListing(tokenId) {
        if (!this.contract || !this.signer) {
            throw new Error('Wallet not connected');
        }

        const tx = await this.contract.cancelListing(tokenId);
        await tx.wait();
        return tx.hash;
    }

    // Buy a listed ticket
    async buyTicket(tokenId, priceInEth) {
        if (!this.contract || !this.signer) {
            throw new Error('Wallet not connected');
        }

        const priceInWei = ethers.parseEther(priceInEth.toString());
        const tx = await this.contract.buyTicket(tokenId, { value: priceInWei });
        await tx.wait();
        return tx.hash;
    }

    // Get current account
    getCurrentAccount() {
        return this.account;
    }

    // Listen for account changes
    onAccountsChanged(callback) {
        if (window.ethereum) {
            window.ethereum.on('accountsChanged', callback);
        }
    }

    // Listen for network changes
    onChainChanged(callback) {
        if (window.ethereum) {
            window.ethereum.on('chainChanged', callback);
        }
    }
}

export default new Web3Service();

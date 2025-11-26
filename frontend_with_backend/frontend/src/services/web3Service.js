import { ethers } from 'ethers';

// Contract ABI - Import from Hardhat artifacts
import TicketManagerArtifact from '../../../smart-contracts/artifacts/contracts/TicketManager.sol/TicketManager.json';

const CONTRACT_ADDRESS = process.env.REACT_APP_CONTRACT_ADDRESS || '0x5FbDB2315678afecb367f032d93F642f64180aa3';
const RPC_URL = process.env.REACT_APP_RPC_URL || 'http://127.0.0.1:8545';

class Web3Service {
    constructor() {
        this.provider = null;
        this.signer = null;
        this.contract = null;
        this.account = null;
    }

    // Connect to MetaMask or other Web3 wallet
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

    // Get read-only provider (no wallet needed)
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

    // Get tickets owned by an address
    async getOwnedTickets(address) {
        if (!this.contract) {
            this.getReadOnlyProvider();
        }

        // Query Transfer events to find tickets owned by address
        const filter = this.contract.filters.Transfer(null, address);
        const events = await this.contract.queryFilter(filter);

        const tokenIds = events.map(event => event.args.tokenId);

        // Get ticket info for each token
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
                    // Token might have been burned or transferred
                    return null;
                }
            })
        );

        return tickets.filter(t => t !== null);
    }

    // List a ticket for resale
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

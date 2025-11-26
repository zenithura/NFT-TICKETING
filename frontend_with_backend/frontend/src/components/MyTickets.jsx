import React, { useState, useEffect } from 'react';
import web3Service from '../services/web3Service';

const MyTickets = ({ walletAddress }) => {
    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [listingPrice, setListingPrice] = useState({});

    useEffect(() => {
        if (walletAddress) {
            loadTickets();
        }
    }, [walletAddress]);

    const loadTickets = async () => {
        setLoading(true);
        try {
            const ownedTickets = await web3Service.getOwnedTickets(walletAddress);
            setTickets(ownedTickets);
        } catch (error) {
            console.error('Error loading tickets:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleListTicket = async (tokenId) => {
        const price = listingPrice[tokenId];
        if (!price || price <= 0) {
            alert('Please enter a valid price');
            return;
        }

        try {
            const txHash = await web3Service.listTicket(tokenId, price);
            alert(`Ticket listed! Transaction: ${txHash}`);
            await loadTickets();
        } catch (error) {
            alert(`Error listing ticket: ${error.message}`);
        }
    };

    const handleCancelListing = async (tokenId) => {
        try {
            const txHash = await web3Service.cancelListing(tokenId);
            alert(`Listing cancelled! Transaction: ${txHash}`);
            await loadTickets();
        } catch (error) {
            alert(`Error cancelling listing: ${error.message}`);
        }
    };

    if (!walletAddress) {
        return (
            <div className="text-center py-8">
                <p className="text-gray-600">Please connect your wallet to view your tickets</p>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="text-center py-8">
                <p className="text-gray-600">Loading tickets...</p>
            </div>
        );
    }

    if (tickets.length === 0) {
        return (
            <div className="text-center py-8">
                <p className="text-gray-600">You don't own any tickets yet</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tickets.map((ticket) => (
                <div key={ticket.tokenId} className="border rounded-lg p-4 shadow-sm">
                    <h3 className="font-bold text-lg mb-2">Ticket #{ticket.tokenId}</h3>
                    <p className="text-sm text-gray-600 mb-1">Event ID: {ticket.eventId}</p>
                    <p className="text-sm text-gray-600 mb-3">
                        Status: {ticket.scanned ? '✅ Used' : '🎫 Active'}
                    </p>

                    {ticket.listing ? (
                        <div className="bg-yellow-50 p-3 rounded mb-3">
                            <p className="text-sm font-semibold">Listed for {ticket.listing.price} ETH</p>
                            <button
                                onClick={() => handleCancelListing(ticket.tokenId)}
                                className="mt-2 w-full px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                            >
                                Cancel Listing
                            </button>
                        </div>
                    ) : !ticket.scanned ? (
                        <div>
                            <input
                                type="number"
                                step="0.01"
                                placeholder="Price in ETH"
                                value={listingPrice[ticket.tokenId] || ''}
                                onChange={(e) => setListingPrice({ ...listingPrice, [ticket.tokenId]: e.target.value })}
                                className="w-full px-3 py-1 border rounded mb-2"
                            />
                            <button
                                onClick={() => handleListTicket(ticket.tokenId)}
                                className="w-full px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                            >
                                List for Resale
                            </button>
                        </div>
                    ) : null}
                </div>
            ))}
        </div>
    );
};

export default MyTickets;

import React, { useState, useEffect } from 'react';
import web3Service from '../services/web3Service';

const WalletConnect = () => {
    const [account, setAccount] = useState(null);
    const [connecting, setConnecting] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Listen for account changes
        web3Service.onAccountsChanged((accounts) => {
            if (accounts.length === 0) {
                setAccount(null);
            } else {
                setAccount(accounts[0]);
            }
        });

        // Listen for network changes
        web3Service.onChainChanged(() => {
            window.location.reload();
        });
    }, []);

    const connectWallet = async () => {
        setConnecting(true);
        setError(null);

        try {
            const address = await web3Service.connectWallet();
            setAccount(address);
        } catch (err) {
            setError(err.message);
        } finally {
            setConnecting(false);
        }
    };

    const formatAddress = (address) => {
        if (!address) return '';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    };

    return (
        <div className="wallet-connect">
            {!account ? (
                <button
                    onClick={connectWallet}
                    disabled={connecting}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                    {connecting ? 'Connecting...' : 'Connect Wallet'}
                </button>
            ) : (
                <div className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-lg">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>{formatAddress(account)}</span>
                </div>
            )}

            {error && (
                <div className="mt-2 text-red-600 text-sm">
                    {error}
                </div>
            )}
        </div>
    );
};

export default WalletConnect;

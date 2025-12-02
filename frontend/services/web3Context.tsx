// File header: Enhanced React context provider for Web3 wallet connection with MetaMask and manual entry.
// Provides wallet address, connection status, balance, user role, and connection methods.

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { UserRole } from '../types';
import { getUser } from './authService';

// Purpose: Declare window.ethereum type for TypeScript.
// Side effects: Extends Window interface.
declare global {
  interface Window {
    ethereum?: {
      isMetaMask?: boolean;
      request: (args: { method: string; params?: any[] }) => Promise<any>;
      on: (event: string, callback: (...args: any[]) => void) => void;
      removeListener: (event: string, callback: (...args: any[]) => void) => void;
      selectedAddress?: string;
      chainId?: string;
    };
  }
}

// Purpose: TypeScript interface defining Web3 context value structure.
// Side effects: None - type definition only.
interface Web3ContextType {
  address: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  connectMetaMask: () => Promise<void>;
  connectManual: (address: string) => Promise<void>;
  disconnect: () => void;
  balance: string;
  userRole: UserRole;
  setUserRole: (role: UserRole) => void;
  provider: 'metamask' | 'manual' | null;
}

// Purpose: Create React context for Web3 state with undefined default.
// Side effects: None - context creation only.
const Web3Context = createContext<Web3ContextType | undefined>(undefined);

// Purpose: Storage keys for localStorage persistence.
const STORAGE_KEY_ADDRESS = 'wallet_address';
const STORAGE_KEY_PROVIDER = 'wallet_provider';

// Purpose: API base URL from environment or default.
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Purpose: Send wallet connection to backend API (optional - doesn't fail if endpoint doesn't exist).
// Params: address (string) - Wallet address, provider (string) - Connection provider type.
// Returns: Promise that resolves with wallet data or void if endpoint doesn't exist.
// Side effects: Makes HTTP POST request to backend (silently fails if endpoint missing).
const syncWithBackend = async (address: string, provider: 'metamask' | 'manual'): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/wallet/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        address: address.toLowerCase(),
        provider,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      // If endpoint doesn't exist (404), just silently skip - wallet connection still works
      if (response.status === 404) {
        console.log('Wallet connect endpoint not available - continuing without backend sync');
        return;
      }
      const errorData = await response.json().catch(() => ({ detail: 'Failed to connect wallet' }));
      throw new Error(errorData.detail || 'Failed to connect wallet');
    }

    const data = await response.json();
    return data;
  } catch (error: any) {
    // Silently handle network errors or missing endpoints - wallet connection still works
    if (error.message?.includes('Failed to fetch') || error.message?.includes('404')) {
      console.log('Wallet backend sync unavailable - continuing without sync');
      return;
    }
    console.error('Backend sync error:', error);
    // Don't throw - allow connection even if backend fails
  }
};

// Purpose: Get ETH balance for an address using Web3 provider.
// Params: address (string) - Wallet address.
// Returns: Promise that resolves with balance string.
// Side effects: Fetches balance from blockchain via Web3 provider.
const getBalance = async (address: string): Promise<string> => {
  try {
    // Try to get balance from Web3 provider if available
    if (typeof window !== 'undefined' && window.ethereum) {
      const provider = window.ethereum;
      const balance = await provider.request({
        method: 'eth_getBalance',
        params: [address, 'latest'],
      });
      // Convert from Wei to ETH (1 ETH = 10^18 Wei)
      const balanceInEth = parseInt(balance, 16) / Math.pow(10, 18);
      return balanceInEth.toFixed(4);
    }
    // Fallback: return 0 if no provider available
    return '0.00';
  } catch (error) {
    console.error('Error fetching balance:', error);
    return '0.00';
  }
};

// Purpose: React context provider component that manages Web3 wallet connection state.
// Params: children (ReactNode) — child components that consume the context.
// Returns: JSX with context provider wrapping children.
// Side effects: Manages wallet state, persists to localStorage, syncs with backend.
export const Web3Provider = ({ children }: { children: ReactNode }) => {
  const [address, setAddress] = useState<string | null>(() => {
    // Purpose: Load persisted address from localStorage on mount.
    // Side effects: Reads from localStorage.
    if (typeof window !== 'undefined') {
      return localStorage.getItem(STORAGE_KEY_ADDRESS);
    }
    return null;
  });

  const [isConnected, setIsConnected] = useState(() => !!address);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [balance, setBalance] = useState('0.00');
  // Initialize userRole from authenticated user's role, fallback to BUYER
  const [userRole, setUserRole] = useState<UserRole>(() => {
    const user = getUser();
    if (user?.role) {
      return user.role.toUpperCase() as UserRole;
    }
    return UserRole.BUYER;
  });
  const [provider, setProvider] = useState<'metamask' | 'manual' | null>(() => {
    // Purpose: Load persisted provider from localStorage on mount.
    // Side effects: Reads from localStorage.
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY_PROVIDER);
      return (stored === 'metamask' || stored === 'manual') ? stored : null;
    }
    return null;
  });

  // Purpose: Update connection state and persist to localStorage.
  // Params: newAddress (string | null) - Wallet address, newProvider ('metamask' | 'manual' | null) - Provider type.
  // Side effects: Updates state, saves to localStorage, syncs with backend.
  const updateConnection = useCallback(async (
    newAddress: string | null,
    newProvider: 'metamask' | 'manual' | null
  ) => {
    if (newAddress) {
      setAddress(newAddress);
      setIsConnected(true);
      setProvider(newProvider);
      setError(null);

      // Persist to localStorage
      localStorage.setItem(STORAGE_KEY_ADDRESS, newAddress);
      if (newProvider) {
        localStorage.setItem(STORAGE_KEY_PROVIDER, newProvider);
      }

      // Sync with backend
      if (newProvider) {
        await syncWithBackend(newAddress, newProvider);
      }

      // Fetch balance
      const balanceValue = await getBalance(newAddress);
      setBalance(balanceValue);
    } else {
      setAddress(null);
      setIsConnected(false);
      setProvider(null);
      setBalance('0.00');
      localStorage.removeItem(STORAGE_KEY_ADDRESS);
      localStorage.removeItem(STORAGE_KEY_PROVIDER);
    }
  }, []);

  // Purpose: Connect wallet using MetaMask extension.
  // Returns: Promise that resolves when connection succeeds or rejects on error.
  // Side effects: Requests MetaMask connection, updates state, syncs with backend.
  const connectMetaMask = useCallback(async () => {
    setIsConnecting(true);
    setError(null);

    try {
      // Check if MetaMask is installed
      if (typeof window === 'undefined' || !window.ethereum || !window.ethereum.isMetaMask) {
        throw new Error('wallet.metaMaskNotFound');
      }

      // Request account access
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts',
      });

      if (!accounts || accounts.length === 0) {
        throw new Error('wallet.noAccountsFound');
      }

      const primaryAccount = accounts[0];

      // Validate address format
      if (!/^0x[a-fA-F0-9]{40}$/.test(primaryAccount)) {
        throw new Error('wallet.invalidAddress');
      }

      // Get chain ID
      const chainId = await window.ethereum.request({ method: 'eth_chainId' });

      // Update connection state
      await updateConnection(primaryAccount, 'metamask');

      // Set up account change listener
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          // User disconnected
          updateConnection(null, null);
        } else if (accounts[0] !== address) {
          // Account changed
          updateConnection(accounts[0], 'metamask');
        }
      };

      // Set up chain change listener
      const handleChainChanged = (chainId: string) => {
        // Reload page on chain change (MetaMask recommendation)
        window.location.reload();
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      // Cleanup listeners on disconnect
      return () => {
        if (window.ethereum) {
          window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
          window.ethereum.removeListener('chainChanged', handleChainChanged);
        }
      };
    } catch (err: any) {
      console.error('MetaMask connection error:', err);

      // Handle specific MetaMask errors
      if (err.code === 4001) {
        setError('wallet.userRejected');
      } else if (err.code === -32002) {
        setError('wallet.requestPending');
      } else if (err.message?.includes('locked')) {
        setError('wallet.metaMaskLocked');
      } else {
        setError(err.message || 'wallet.connectionFailed');
      }
      throw err;
    } finally {
      setIsConnecting(false);
    }
  }, [address, updateConnection]);

  // Purpose: Connect wallet using manual address entry.
  // Params: address (string) - Ethereum wallet address.
  // Returns: Promise that resolves when connection succeeds or rejects on error.
  // Side effects: Validates address, updates state, syncs with backend.
  const connectManual = useCallback(async (addressInput: string) => {
    setIsConnecting(true);
    setError(null);

    try {
      const trimmed = addressInput.trim().toLowerCase();

      // Validate address format
      if (!/^0x[a-fA-F0-9]{40}$/.test(trimmed)) {
        throw new Error('wallet.invalidAddress');
      }

      // Update connection state
      await updateConnection(trimmed, 'manual');
    } catch (err: any) {
      console.error('Manual connection error:', err);
      setError(err.message || 'wallet.connectionFailed');
      throw err;
    } finally {
      setIsConnecting(false);
    }
  }, [updateConnection]);

  // Purpose: Disconnect wallet and reset all connection state.
  // Side effects: Clears address, sets connected to false, resets balance, clears localStorage.
  // Note: userRole is preserved from authenticated user's role (handled by useEffect).
  const disconnect = useCallback(() => {
    updateConnection(null, null);
    // Keep userRole synced with authenticated user (handled by useEffect)
    setError(null);
  }, [updateConnection]);

  // Purpose: Restore connection from localStorage on mount.
  // Side effects: Restores persisted connection if available.
  useEffect(() => {
    const storedAddress = localStorage.getItem(STORAGE_KEY_ADDRESS);
    const storedProvider = localStorage.getItem(STORAGE_KEY_PROVIDER) as 'metamask' | 'manual' | null;

    if (storedAddress && storedProvider) {
      if (storedProvider === 'metamask') {
        // For MetaMask, verify the connection is still valid
        if (window.ethereum?.isMetaMask && window.ethereum.selectedAddress) {
          if (window.ethereum.selectedAddress.toLowerCase() === storedAddress.toLowerCase()) {
            updateConnection(storedAddress, 'metamask');
          } else {
            // Address changed, update it
            updateConnection(window.ethereum.selectedAddress, 'metamask');
          }
        } else {
          // MetaMask not available, clear connection
          disconnect();
        }
      } else if (storedProvider === 'manual') {
        // Manual connection persists
        updateConnection(storedAddress, 'manual');
      }
    }
  }, [updateConnection, disconnect]);

  // Purpose: Sync userRole with authenticated user's role when user changes.
  // Side effects: Updates userRole state when authenticated user changes.
  // Note: This runs on mount and when localStorage changes, syncing role from auth context.
  useEffect(() => {
    const syncUserRole = () => {
      const user = getUser();
      if (user?.role) {
        const newRole = user.role.toUpperCase() as UserRole;
        setUserRole(prevRole => {
          if (prevRole !== newRole) {
            return newRole;
          }
          return prevRole;
        });
      }
    };
    
    // Sync on mount
    syncUserRole();
    
    // Listen for storage changes (when user logs in/out)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'user' || e.key === 'access_token') {
        syncUserRole();
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <Web3Context.Provider
      value={{
        address,
        isConnected,
        isConnecting,
        error,
        connectMetaMask,
        connectManual,
        disconnect,
        balance,
        userRole,
        setUserRole,
        provider,
      }}
    >
      {children}
    </Web3Context.Provider>
  );
};

// Purpose: React hook to access Web3 context from child components.
// Returns: Web3ContextType object with wallet state and methods.
// Side effects: Throws error if used outside Web3Provider.
export const useWeb3 = () => {
  const context = useContext(Web3Context);
  if (context === undefined) {
    throw new Error('useWeb3 must be used within a Web3Provider');
  }
  return context;
};

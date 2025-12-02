// File header: React context provider for Web3 wallet connection state management.
// Provides wallet address, connection status, balance, and user role to child components.

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { UserRole } from '../types';

// Purpose: TypeScript interface defining Web3 context value structure.
// Side effects: None - type definition only.
interface Web3ContextType {
  address: string | null;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  balance: string;
  userRole: UserRole;
  setUserRole: (role: UserRole) => void;
}

// Purpose: Create React context for Web3 state with undefined default.
// Side effects: None - context creation only.
const Web3Context = createContext<Web3ContextType | undefined>(undefined);

// Purpose: React context provider component that manages Web3 wallet connection state.
// Params: children (ReactNode) — child components that consume the context.
// Returns: JSX with context provider wrapping children.
// Side effects: Manages wallet state, provides mock connection for demo purposes.
export const Web3Provider = ({ children }: { children: ReactNode }) => {
  const [address, setAddress] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [balance, setBalance] = useState('0.00');
  // Purpose: Default role is BUYER for new wallet connections.
  const [userRole, setUserRole] = useState<UserRole>(UserRole.BUYER);

  // Purpose: Simulate wallet connection with mock address and balance.
  // Returns: Promise that resolves after simulated delay.
  // Side effects: Updates address, connection status, and balance state.
  const connect = async () => {
    // Purpose: Simulate network delay for wallet connection (e.g., MetaMask).
    await new Promise(resolve => setTimeout(resolve, 800));
    const mockAddress = '0x71C...9A23';
    setAddress(mockAddress);
    setIsConnected(true);
    setBalance('1.45'); // Mock ETH balance
  };

  // Purpose: Disconnect wallet and reset all connection state.
  // Side effects: Clears address, sets connected to false, resets balance and role.
  const disconnect = () => {
    setAddress(null);
    setIsConnected(false);
    setBalance('0.00');
    setUserRole(UserRole.BUYER); // Reset role on disconnect
  };

  return (
    <Web3Context.Provider value={{ address, isConnected, connect, disconnect, balance, userRole, setUserRole }}>
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
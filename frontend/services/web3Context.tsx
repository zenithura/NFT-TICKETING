import React, { createContext, useContext, useState, ReactNode } from 'react';
import { UserRole } from '../types';

interface Web3ContextType {
  address: string | null;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  balance: string;
  userRole: UserRole;
  setUserRole: (role: UserRole) => void;
}

const Web3Context = createContext<Web3ContextType | undefined>(undefined);

export const Web3Provider = ({ children }: { children: ReactNode }) => {
  const [address, setAddress] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [balance, setBalance] = useState('0.00');
  // Default role is BUYER for new connections
  const [userRole, setUserRole] = useState<UserRole>(UserRole.BUYER);

  const connect = async () => {
    // Simulate a delay for wallet connection (e.g., MetaMask)
    await new Promise(resolve => setTimeout(resolve, 800));
    const mockAddress = '0x71C...9A23';
    setAddress(mockAddress);
    setIsConnected(true);
    setBalance('1.45'); // Mock ETH balance
  };

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

export const useWeb3 = () => {
  const context = useContext(Web3Context);
  if (context === undefined) {
    throw new Error('useWeb3 must be used within a Web3Provider');
  }
  return context;
};
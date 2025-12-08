// File header: React context provider for authentication state management.
// Provides authentication state, user information, and auth methods to child components.

/**
 * Authentication context for NFT Ticketing Platform.
 * Manages user authentication state and provides auth methods.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  LoginData,
  RegisterData,
  login as loginAPI,
  register as registerAPI,
  logout as logoutAPI,
  getCurrentUser,
  isAuthenticated,
  getUser as getStoredUser,
  clearAuth,
} from './authService';
import { authToasts } from '../lib/toastService';

// Purpose: Interface for authentication context value.
// Side effects: None - type definition only.
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// Purpose: Create React context for authentication state.
// Side effects: None - context creation only.
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Purpose: React context provider component for authentication.
// Params: children (ReactNode) — child components.
// Returns: JSX with context provider.
// Side effects: Manages authentication state, loads user on mount.
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false); // Start as false to not block render

  // Purpose: Load user from storage and verify token on mount.
  // Side effects: Reads from localStorage, calls API to verify token.
  // Non-blocking: Sets user immediately from storage, verifies in background
  useEffect(() => {
    const loadUser = async () => {
      try {
        if (isAuthenticated()) {
          const storedUser = getStoredUser();
          if (storedUser) {
            // Set user immediately from storage (non-blocking)
            setUser(storedUser);
            // Verify token in background (non-blocking)
            getCurrentUser().catch(() => {
              clearAuth();
              setUser(null);
            });
          }
        }
      } catch (error) {
        console.error('Error loading user:', error);
        clearAuth();
        setUser(null);
      }
      // Don't set isLoading - render immediately
    };

    // Use requestIdleCallback or setTimeout to defer slightly
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(loadUser, { timeout: 100 });
    } else {
      setTimeout(loadUser, 0);
    }
  }, []);

  // Purpose: Login user and update state.
  // Params: data (LoginData) — login credentials.
  // Returns: Promise that resolves when login is complete.
  // Side effects: Updates user state, stores tokens.
  const login = async (data: LoginData): Promise<void> => {
    try {
      const response = await loginAPI(data);
      if (response.user) {
        setUser(response.user);
      }
    } catch (error) {
      throw error;
    }
  };

  // Purpose: Register new user and update state.
  // Params: data (RegisterData) — registration information.
  // Returns: Promise that resolves when registration is complete.
  // Side effects: Updates user state, stores tokens.
  const register = async (data: RegisterData): Promise<void> => {
    try {
      const response = await registerAPI(data);
      if (response.user) {
        setUser(response.user);
      }
    } catch (error) {
      throw error;
    }
  };

  // Purpose: Logout user and clear state.
  // Returns: Promise that resolves when logout is complete.
  // Side effects: Clears user state and tokens.
  const logout = async (): Promise<void> => {
    try {
      await logoutAPI();
      authToasts.logoutSuccess();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      clearAuth();
    }
  };

  // Purpose: Refresh user information from API.
  // Returns: Promise that resolves when user is refreshed.
  // Side effects: Updates user state with latest information.
  const refreshUser = async (): Promise<void> => {
    try {
      const updatedUser = await getCurrentUser();
      setUser(updatedUser);
    } catch (error) {
      console.error('Error refreshing user:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Purpose: Hook to access authentication context.
// Returns: AuthContextType value.
// Side effects: Throws error if used outside AuthProvider.
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};


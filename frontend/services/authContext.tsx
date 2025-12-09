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
  const [isLoading, setIsLoading] = useState(true); // Start as true to prevent premature redirects

  // Purpose: Load user from storage and verify token on mount.
  // Side effects: Reads from localStorage, calls API to verify token.
  // Ensures proper authentication state before rendering protected routes
  useEffect(() => {
    const loadUser = async () => {
      setIsLoading(true);
      try {
        // Check if token exists first
        if (isAuthenticated()) {
          const storedUser = getStoredUser();
          if (storedUser) {
            // Set user immediately from storage (optimistic loading)
            setUser(storedUser);
            
            // Verify token validity with server (non-blocking, but wait for result)
            try {
              const verifiedUser = await getCurrentUser();
              // Only update if verification succeeds
              setUser(verifiedUser);
            } catch (verifyError) {
              // Token is invalid or expired - only clear if verification fails
              console.warn('Token verification failed:', verifyError);
              // Don't clear auth immediately - let the request retry with refresh token
              // Only clear if both token and refresh token are invalid
              // The authenticatedFetch will handle token refresh
            }
          } else {
            // Token exists but no user data - verify token to get user
            try {
              const verifiedUser = await getCurrentUser();
              setUser(verifiedUser);
            } catch (verifyError) {
              console.warn('Failed to verify token:', verifyError);
              // Don't clear auth here - token might still be valid, just failed to fetch user
              // This prevents race conditions where token is valid but user fetch fails
            }
          }
        } else {
          // No token - definitely not authenticated
          setUser(null);
        }
      } catch (error) {
        console.error('Error loading user:', error);
        // Only clear auth if we're certain there's no valid token
        const hasToken = isAuthenticated();
        if (!hasToken) {
          clearAuth();
          setUser(null);
        }
        // If token exists, keep user state (might be network error, not auth error)
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
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

  // Purpose: Determine authentication status.
  // Checks both token existence and user object to prevent false negatives.
  // This ensures authenticated users don't get redirected incorrectly.
  // Uses token check from authService to validate presence of access token.
  const isAuthenticatedState: boolean = !!user || isAuthenticated();

  const value: AuthContextType = {
    user,
    isAuthenticated: isAuthenticatedState,
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


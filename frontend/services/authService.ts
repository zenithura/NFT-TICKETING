// File header: Authentication service for managing user authentication state and API calls.
// Handles login, registration, token management, and authentication state persistence.

/**
 * Authentication service for NFT Ticketing Platform.
 * Manages JWT tokens, user state, and API communication.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Purpose: Interface for authentication response from API.
// Side effects: None - type definition only.
export interface AuthResponse {
  success: boolean;
  message: string;
  access_token?: string;
  refresh_token?: string;
  user?: User;
}

// Purpose: Interface for user information.
// Side effects: None - type definition only.
export interface User {
  user_id: number;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  role: string;
  is_email_verified: boolean;
  created_at: string;
}

// Purpose: Interface for login request data.
// Side effects: None - type definition only.
export interface LoginData {
  email: string;
  password: string;
}

// Purpose: Interface for registration request data.
// Side effects: None - type definition only.
export interface RegisterData {
  email: string;
  password: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  role: 'BUYER' | 'ORGANIZER'; // Required role selection during signup
}

// Purpose: Get stored access token from localStorage.
// Returns: Access token string or null.
// Side effects: Reads from localStorage.
export const getAccessToken = (): string | null => {
  return localStorage.getItem('access_token');
};

// Purpose: Get stored refresh token from localStorage.
// Returns: Refresh token string or null.
// Side effects: Reads from localStorage.
export const getRefreshToken = (): string | null => {
  return localStorage.getItem('refresh_token');
};

// Purpose: Store access token in localStorage.
// Params: token (string) — JWT access token.
// Side effects: Writes to localStorage.
export const setAccessToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

// Purpose: Store refresh token in localStorage.
// Params: token (string) — JWT refresh token.
// Side effects: Writes to localStorage.
export const setRefreshToken = (token: string): void => {
  localStorage.setItem('refresh_token', token);
};

// Purpose: Store user information in localStorage.
// Params: user (User) — user object.
// Side effects: Writes to localStorage.
export const setUser = (user: User): void => {
  localStorage.setItem('user', JSON.stringify(user));
};

// Purpose: Get stored user information from localStorage.
// Returns: User object or null.
// Side effects: Reads from localStorage.
export const getUser = (): User | null => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

// Purpose: Clear all authentication data from localStorage.
// Side effects: Removes tokens and user data from localStorage.
export const clearAuth = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

// Purpose: Check if user is authenticated (has valid token).
// Returns: True if access token exists, False otherwise.
// Side effects: None - checks localStorage only.
export const isAuthenticated = (): boolean => {
  return !!getAccessToken();
};

// Purpose: Make authenticated API request with automatic token refresh.
// Params: url (string) — API endpoint; options (RequestInit) — fetch options.
// Returns: Promise with Response object.
// Side effects: Adds Authorization header, refreshes token if expired.
export const authenticatedFetch = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const token = getAccessToken();
  
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  let response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });
  
  // Purpose: If token expired, try to refresh it.
  // Side effects: Calls refresh token endpoint, retries original request.
  if (response.status === 401) {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        
        if (refreshResponse.ok) {
          const data: AuthResponse = await refreshResponse.json();
          if (data.access_token) {
            setAccessToken(data.access_token);
            if (data.refresh_token) {
              setRefreshToken(data.refresh_token);
            }
            
            // Retry original request with new token
            headers.set('Authorization', `Bearer ${data.access_token}`);
            response = await fetch(`${API_BASE_URL}${url}`, {
              ...options,
              headers,
            });
          }
        } else {
          // Refresh failed, clear auth
          clearAuth();
          throw new Error('Session expired. Please login again.');
        }
      } catch (error) {
        clearAuth();
        throw error;
      }
    } else {
      clearAuth();
    }
  }
  
  return response;
};

// Purpose: Register new user account.
// Params: data (RegisterData) — registration information.
// Returns: Promise with AuthResponse.
// Side effects: Creates user account, stores tokens and user data.
export const register = async (data: RegisterData): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  
  const result: AuthResponse = await response.json();
  
  if (!response.ok) {
    throw new Error(result.message || 'Registration failed');
  }
  
  if (result.access_token && result.refresh_token && result.user) {
    setAccessToken(result.access_token);
    setRefreshToken(result.refresh_token);
    setUser(result.user);
  }
  
  return result;
};

// Purpose: Login user and get authentication tokens.
// Params: data (LoginData) — login credentials.
// Returns: Promise with AuthResponse.
// Side effects: Stores tokens and user data on successful login.
export const login = async (data: LoginData): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  
  const result: AuthResponse = await response.json();
  
  if (!response.ok) {
    throw new Error(result.message || 'Login failed');
  }
  
  if (result.access_token && result.refresh_token && result.user) {
    setAccessToken(result.access_token);
    setRefreshToken(result.refresh_token);
    setUser(result.user);
  }
  
  return result;
};

// Purpose: Logout user and clear authentication data.
// Returns: Promise that resolves when logout is complete.
// Side effects: Clears tokens and user data, invalidates refresh token.
export const logout = async (): Promise<void> => {
  const token = getAccessToken();
  
  if (token) {
    try {
      await authenticatedFetch('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: getRefreshToken() }),
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  }
  
  clearAuth();
};

// Purpose: Request password reset email.
// Params: email (string) — user email address.
// Returns: Promise with success message.
// Side effects: Sends password reset email.
export const forgotPassword = async (email: string): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  
  const result: AuthResponse = await response.json();
  
  if (!response.ok) {
    throw new Error(result.message || 'Failed to send reset email');
  }
  
  return result;
};

// Purpose: Reset password using reset token.
// Params: token (string) — reset token from email; newPassword (string) — new password.
// Returns: Promise with success message.
// Side effects: Updates user password, invalidates all tokens.
export const resetPassword = async (token: string, newPassword: string): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  
  const result: AuthResponse = await response.json();
  
  if (!response.ok) {
    throw new Error(result.message || 'Password reset failed');
  }
  
  return result;
};

// Purpose: Verify email address using verification token.
// Params: token (string) — verification token from email.
// Returns: Promise with success message.
// Side effects: Marks email as verified.
export const verifyEmail = async (token: string): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/verify-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  });
  
  const result: AuthResponse = await response.json();
  
  if (!response.ok) {
    throw new Error(result.message || 'Email verification failed');
  }
  
  return result;
};

// Purpose: Get current authenticated user information.
// Returns: Promise with User object.
// Side effects: Updates stored user data if changed.
export const getCurrentUser = async (): Promise<User> => {
  const response = await authenticatedFetch('/auth/me');
  
  if (!response.ok) {
    if (response.status === 401) {
      clearAuth();
    }
    throw new Error('Failed to get user information');
  }
  
  const user: User = await response.json();
  setUser(user);
  
  return user;
};


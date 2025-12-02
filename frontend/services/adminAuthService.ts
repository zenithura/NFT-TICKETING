/**
 * Admin Authentication Service
 * Handles admin login, session management, and authentication state
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface AdminLoginResponse {
  success: boolean;
  message: string;
  admin?: {
    username: string;
    role: string;
  };
}

/**
 * Admin login with username and password
 */
export const adminLogin = async (username: string, password: string): Promise<AdminLoginResponse> => {
  const response = await fetch(`${API_BASE_URL}/admin/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Important for cookies
    body: JSON.stringify({ username, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Login failed');
  }

  return data;
};

/**
 * Check if admin session is valid
 */
export const checkAdminSession = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/session`, {
      method: 'GET',
      credentials: 'include', // Important for cookies
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.authenticated === true;
  } catch (error) {
    return false;
  }
};

/**
 * Get current admin user info
 */
export const getAdminUser = async (): Promise<any> => {
  const response = await fetch(`${API_BASE_URL}/admin/session`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Not authenticated');
  }

  return response.json();
};

/**
 * Admin logout
 */
export const adminLogout = async (): Promise<void> => {
  try {
    await fetch(`${API_BASE_URL}/admin/logout`, {
      method: 'POST',
      credentials: 'include',
    });
  } catch (error) {
    console.error('Logout error:', error);
  }
};

/**
 * Make authenticated admin API request
 */
export const adminAuthenticatedFetch = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    credentials: 'include', // Important for cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  // If unauthorized, redirect to login
  if (response.status === 401) {
    window.location.href = '/admin/login';
    throw new Error('Unauthorized');
  }

  return response;
};


/**
 * Admin service for managing security alerts, bans, and dashboard statistics.
 * Provides API methods for admin dashboard functionality.
 */

import { adminAuthenticatedFetch } from './adminAuthService';

// Use relative URL when proxying, or full URL if VITE_API_URL is set
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Types
export interface SecurityAlert {
  alert_id: number;
  user_id: number | null;
  ip_address: string;
  attack_type: string;
  payload: string | null;
  endpoint: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  status: 'NEW' | 'REVIEWED' | 'BANNED' | 'IGNORED' | 'FALSE_POSITIVE';
  user_agent: string | null;
  country_code: string | null;
  city: string | null;
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: number | null;
}

export interface AdminStats {
  total_users: number;
  total_alerts_24h: number;
  total_alerts_7d: number;
  total_alerts_30d: number;
  critical_alerts_24h: number;
  banned_users: number;
  banned_ips: number;
  system_health: 'HEALTHY' | 'CAUTION' | 'WARNING' | 'CRITICAL';
}

export interface GraphData {
  alerts_by_type: Record<string, number>;
  alerts_by_severity: Record<string, number>;
  alerts_timeline: Array<{ date: string; count: number }>;
  top_attacking_ips: Array<{ ip: string; count: number }>;
  top_attacked_endpoints: Array<{ endpoint: string; count: number }>;
}

export interface BanRequest {
  user_id?: number;
  ip_address?: string;
  ban_reason: string;
  ban_duration?: 'TEMPORARY' | 'PERMANENT';
  expires_hours?: number;
  notes?: string;
}

export interface AlertFilters {
  skip?: number;
  limit?: number;
  severity?: string;
  attack_type?: string;
  status?: string;
  ip_address?: string;
  user_id?: number;
  start_date?: string;
  end_date?: string;
}

export interface WebRequest {
  request_id: number;
  user_id: number | null;
  username: string | null;
  ip_address: string;
  http_method: string;
  path: string;
  endpoint: string | null;
  response_status: number | null;
  response_time_ms: number | null;
  user_agent: string | null;
  is_authenticated: boolean;
  created_at: string;
}

export interface WebRequestFilters {
  user_id?: number;
  username?: string;
  ip_address?: string;
  http_method?: string;
  path?: string;
  endpoint?: string;
  status_code?: number;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}

export interface User {
  user_id: number;
  email: string;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  role: string;
  is_email_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export interface UserCreateRequest {
  email: string;
  password: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  role?: string;
}

export interface UserUpdateRequest {
  email?: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  role?: string;
  is_active?: boolean;
  is_email_verified?: boolean;
}

export interface SOARConfig {
  config_id: number;
  platform_name: string;
  endpoint_url: string;
  is_enabled: boolean;
  event_types: string[];
  severity_filter: string[];
  retry_count: number;
  timeout_seconds: number;
  verify_ssl: boolean;
  custom_headers: Record<string, any>;
  created_at: string;
  updated_at: string;
}

/**
 * Get admin dashboard statistics.
 */
export const getAdminStats = async (): Promise<AdminStats> => {
  const response = await adminAuthenticatedFetch('/admin/stats');
  if (!response.ok) {
    throw new Error('Failed to fetch admin stats');
  }
  return response.json();
};

/**
 * Get security alerts with optional filters.
 */
export const getAlerts = async (filters: AlertFilters = {}): Promise<SecurityAlert[]> => {
  const params = new URLSearchParams();
  if (filters.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
  if (filters.severity) params.append('severity', filters.severity);
  if (filters.attack_type) params.append('attack_type', filters.attack_type);
  if (filters.status) params.append('status_filter', filters.status);
  if (filters.ip_address) params.append('ip_address', filters.ip_address);
  if (filters.user_id) params.append('user_id', filters.user_id.toString());
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);

  const response = await adminAuthenticatedFetch(`/admin/alerts?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch alerts');
  }
  return response.json();
};

/**
 * Get specific alert details.
 */
export const getAlert = async (alertId: number): Promise<SecurityAlert> => {
  const response = await adminAuthenticatedFetch(`/admin/alerts/${alertId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch alert');
  }
  return response.json();
};

/**
 * Update alert status.
 */
export const updateAlertStatus = async (
  alertId: number,
  status: 'REVIEWED' | 'IGNORED' | 'BANNED' | 'FALSE_POSITIVE'
): Promise<SecurityAlert> => {
  const response = await adminAuthenticatedFetch(`/admin/alerts/${alertId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
  if (!response.ok) {
    throw new Error('Failed to update alert status');
  }
  return response.json();
};

/**
 * Ban a user or IP address.
 */
export const banUserOrIp = async (banRequest: BanRequest): Promise<{ success: boolean; message: string }> => {
  const response = await adminAuthenticatedFetch('/admin/ban', {
    method: 'POST',
    body: JSON.stringify(banRequest),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to ban user/IP');
  }
  return response.json();
};

/**
 * Unban a user or IP address.
 */
export const unbanUserOrIp = async (user_id?: number, ip_address?: string): Promise<{ success: boolean; message: string }> => {
  const response = await adminAuthenticatedFetch('/admin/unban', {
    method: 'POST',
    body: JSON.stringify({ user_id, ip_address }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to unban user/IP');
  }
  return response.json();
};

/**
 * Get graph data for dashboard charts.
 */
export const getGraphData = async (days: number = 7): Promise<GraphData> => {
  const response = await adminAuthenticatedFetch(`/admin/graph-data?days=${days}`);
  if (!response.ok) {
    throw new Error('Failed to fetch graph data');
  }
  return response.json();
};

/**
 * Export alerts as JSON or CSV.
 */
export const exportAlerts = async (format: 'json' | 'csv' = 'json', start_date?: string, end_date?: string): Promise<Blob> => {
  const params = new URLSearchParams();
  params.append('format', format);
  if (start_date) params.append('start_date', start_date);
  if (end_date) params.append('end_date', end_date);

  const response = await adminAuthenticatedFetch(`/admin/export-alerts?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to export alerts');
  }
  return response.blob();
};

/**
 * Get all users (admin only).
 */
export const getAllUsers = async (skip: number = 0, limit: number = 50, search?: string): Promise<User[]> => {
  const params = new URLSearchParams();
  params.append('skip', skip.toString());
  params.append('limit', limit.toString());
  if (search) params.append('search', search);

  const response = await adminAuthenticatedFetch(`/admin/users?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }
  return response.json();
};

// ============================================================================
// Web Requests
// ============================================================================

export interface WebRequestsResponse {
  skip: number;
  limit: number;
  total: number;
  results: WebRequest[];
}

/**
 * Get web requests with filtering.
 */
export const getWebRequests = async (filters: WebRequestFilters = {}): Promise<WebRequestsResponse> => {
  const params = new URLSearchParams();
  if (filters.user_id) params.append('user_id', filters.user_id.toString());
  if (filters.username) params.append('username', filters.username);
  if (filters.ip_address) params.append('ip_address', filters.ip_address);
  if (filters.http_method) params.append('http_method', filters.http_method);
  if (filters.path) params.append('path', filters.path);
  if (filters.endpoint) params.append('endpoint', filters.endpoint);
  if (filters.status_code) params.append('status_code', filters.status_code.toString());
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);
  if (filters.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters.limit !== undefined) params.append('limit', filters.limit.toString());

  const response = await adminAuthenticatedFetch(`/admin/web-requests?${params.toString()}`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch web requests' }));
    throw new Error(error.detail || 'Failed to fetch web requests');
  }
  return response.json();
};

/**
 * Export web requests as JSON or CSV.
 */
export const exportWebRequests = async (format: 'json' | 'csv' = 'json', start_date?: string, end_date?: string): Promise<Blob> => {
  const params = new URLSearchParams();
  params.append('format', format);
  if (start_date) params.append('start_date', start_date);
  if (end_date) params.append('end_date', end_date);

  const response = await adminAuthenticatedFetch(`/admin/web-requests/export?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to export web requests');
  }
  return response.blob();
};

/**
 * Clear old web requests.
 */
export const clearWebRequests = async (days: number = 90): Promise<{ success: boolean; message: string; deleted_count: number }> => {
  const response = await adminAuthenticatedFetch(`/admin/web-requests/clear?days=${days}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to clear web requests');
  }
  return response.json();
};

/**
 * Clear all alerts.
 */
export const clearAllAlerts = async (): Promise<{ success: boolean; message: string; deleted_count: number }> => {
  const response = await adminAuthenticatedFetch('/admin/alerts/clear', {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to clear alerts');
  }
  return response.json();
};

// ============================================================================
// Users Management
// ============================================================================

/**
 * Create a new user.
 */
export const createUser = async (userData: UserCreateRequest): Promise<User> => {
  const response = await adminAuthenticatedFetch('/admin/users', {
    method: 'POST',
    body: JSON.stringify(userData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create user');
  }
  return response.json();
};

/**
 * Update user.
 */
export const updateUser = async (userId: number, userData: UserUpdateRequest): Promise<User> => {
  const response = await adminAuthenticatedFetch(`/admin/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(userData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update user');
  }
  return response.json();
};

/**
 * Delete user.
 */
export const deleteUser = async (userId: number): Promise<{ success: boolean; message: string }> => {
  const response = await adminAuthenticatedFetch(`/admin/users/${userId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete user');
  }
  return response.json();
};

/**
 * Reset user password.
 */
export const resetUserPassword = async (userId: number, newPassword: string): Promise<{ success: boolean; message: string }> => {
  const response = await adminAuthenticatedFetch(`/admin/users/${userId}/reset-password`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, new_password: newPassword }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reset password');
  }
  return response.json();
};

/**
 * Get user activity log.
 */
export const getUserActivity = async (userId: number, skip: number = 0, limit: number = 50): Promise<any[]> => {
  const params = new URLSearchParams();
  params.append('skip', skip.toString());
  params.append('limit', limit.toString());

  const response = await adminAuthenticatedFetch(`/admin/users/${userId}/activity?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch user activity');
  }
  return response.json();
};

// ============================================================================
// SOAR Configuration
// ============================================================================

/**
 * Get all SOAR configurations.
 */
export const getSOARConfigs = async (): Promise<SOARConfig[]> => {
  const response = await adminAuthenticatedFetch('/admin/soar/config');
  if (!response.ok) {
    throw new Error('Failed to fetch SOAR configs');
  }
  return response.json();
};

/**
 * Create SOAR configuration.
 */
export const createSOARConfig = async (config: Partial<SOARConfig>): Promise<SOARConfig> => {
  const response = await adminAuthenticatedFetch('/admin/soar/config', {
    method: 'POST',
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create SOAR config');
  }
  return response.json();
};

/**
 * Update SOAR configuration.
 */
export const updateSOARConfig = async (configId: number, config: Partial<SOARConfig>): Promise<SOARConfig> => {
  const response = await adminAuthenticatedFetch(`/admin/soar/config/${configId}`, {
    method: 'PATCH',
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update SOAR config');
  }
  return response.json();
};

/**
 * Delete SOAR configuration.
 */
export const deleteSOARConfig = async (configId: number): Promise<{ success: boolean; message: string }> => {
  const response = await adminAuthenticatedFetch(`/admin/soar/config/${configId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete SOAR config');
  }
  return response.json();
};

/**
 * Test SOAR configuration connection.
 */
export const testSOARConnection = async (configId: number): Promise<{ success: boolean; message: string }> => {
  const response = await adminAuthenticatedFetch(`/admin/soar/config/${configId}/test`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Connection test failed');
  }
  return response.json();
};


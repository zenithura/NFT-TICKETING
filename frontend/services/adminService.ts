/**
 * Admin service for managing security alerts, bans, and dashboard statistics.
 * Provides API methods for admin dashboard functionality.
 */

import { adminAuthenticatedFetch } from './adminAuthService';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

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
export const getAllUsers = async (skip: number = 0, limit: number = 50, search?: string): Promise<any[]> => {
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


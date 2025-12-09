/**
 * Admin Dashboard with Security Alerts System
 * Provides comprehensive security monitoring, alert management, and system administration.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { checkAdminSession, adminLogout, getAdminUser } from '../services/adminAuthService';
import { adminToasts } from '../lib/toastService';
import {
  Shield,
  AlertTriangle,
  Users,
  Activity,
  Ban,
  CheckCircle,
  XCircle,
  Filter,
  Download,
  RefreshCw,
  Bell,
  TrendingUp,
  Globe,
  Server,
  Lock,
  Eye,
  EyeOff,
} from 'lucide-react';
import {
  getAdminStats,
  getAlerts,
  getAlert,
  updateAlertStatus,
  banUserOrIp,
  unbanUserOrIp,
  getGraphData,
  exportAlerts,
  getAllUsers,
  getWebRequests,
  exportWebRequests,
  clearWebRequests,
  clearAllAlerts,
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  getUserActivity,
  getSOARConfigs,
  createSOARConfig,
  updateSOARConfig,
  deleteSOARConfig,
  testSOARConnection,
  type SecurityAlert,
  type AdminStats,
  type GraphData,
  type AlertFilters,
  type WebRequest,
  type WebRequestFilters,
  type User,
  type UserCreateRequest,
  type UserUpdateRequest,
  type SOARConfig,
} from '../services/adminService';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

type TabType = 'overview' | 'alerts' | 'users' | 'web-requests' | 'soar';

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#6b7280',
};

const STATUS_COLORS = {
  NEW: '#3b82f6',
  REVIEWED: '#10b981',
  BANNED: '#ef4444',
  IGNORED: '#6b7280',
  FALSE_POSITIVE: '#8b5cf6',
};

export const AdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [adminUser, setAdminUser] = useState<any>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [alertLoading, setAlertLoading] = useState(false);
  const [newAlertsCount, setNewAlertsCount] = useState(0);
  const [filters, setFilters] = useState<AlertFilters>({
    skip: 0,
    limit: 50,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Check admin authentication
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const authenticated = await checkAdminSession();
        if (!authenticated) {
          navigate('/secure-admin/login', { replace: true });
          return;
        }
        const user = await getAdminUser();
        setAdminUser(user.admin);
        setIsAuthenticated(true);
      } catch (error) {
        navigate('/secure-admin/login', { replace: true });
      } finally {
        setIsCheckingAuth(false);
      }
    };
    checkAuth();
  }, [navigate]);

  // Handle logout
  const handleLogout = async () => {
    try {
      await adminLogout();
      adminToasts.logoutSuccess();
      navigate('/secure-admin/login', { replace: true });
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/secure-admin/login', { replace: true });
    }
  };

  // Load dashboard data
  const loadDashboardData = useCallback(async () => {
    if (!isAuthenticated || isCheckingAuth) return;

    try {
      setLoading(true);
      const [statsData, alertsData, graphDataResponse] = await Promise.all([
        getAdminStats(),
        getAlerts(filters),
        getGraphData(7),
      ]);
      setStats(statsData);
      
      // DEDUPLICATION: Remove duplicates based on alert_id
      const uniqueAlerts = alertsData.filter((alert, index, self) =>
        index === self.findIndex((a) => a.alert_id === alert.alert_id)
      );
      setAlerts(uniqueAlerts);
      
      setGraphData(graphDataResponse);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, isCheckingAuth, filters]);

  // Load alerts
  const loadAlerts = useCallback(async () => {
    if (!isAuthenticated || isCheckingAuth) return;

    try {
      setAlertLoading(true);
      const alertsData = await getAlerts(filters);
      
      // DEDUPLICATION: Remove duplicates based on alert_id
      // This ensures we don't show the same alert multiple times
      const uniqueAlerts = alertsData.filter((alert, index, self) =>
        index === self.findIndex((a) => a.alert_id === alert.alert_id)
      );
      
      setAlerts(uniqueAlerts);
      
      // Count new alerts
      const newCount = uniqueAlerts.filter(a => a.status === 'NEW').length;
      setNewAlertsCount(newCount);
    } catch (error) {
      console.error('Failed to load alerts:', error);
    } finally {
      setAlertLoading(false);
    }
  }, [isAuthenticated, isCheckingAuth, filters]);

  // Auto-refresh alerts
  useEffect(() => {
    if (!isAuthenticated || !autoRefresh) return;

    loadAlerts();
    const interval = setInterval(loadAlerts, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [isAuthenticated, autoRefresh, loadAlerts]);

  // Initial load
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Handle alert status update
  const handleUpdateAlertStatus = async (alertId: number, status: string) => {
    try {
      await updateAlertStatus(alertId, status as any);
      await loadAlerts();
      if (selectedAlert?.alert_id === alertId) {
        const updated = await getAlert(alertId);
        setSelectedAlert(updated);
      }
      adminToasts.alertUpdated();
    } catch (error) {
      console.error('Failed to update alert status:', error);
      alert('Failed to update alert status');
    }
  };

  // Handle ban
  const handleBan = async (alert: SecurityAlert) => {
    if (!confirm(`Are you sure you want to ban ${alert.user_id ? 'user' : 'IP'} ${alert.user_id || alert.ip_address}?`)) {
      return;
    }

    try {
      await banUserOrIp({
        user_id: alert.user_id || undefined,
        ip_address: alert.ip_address,
        ban_reason: `Banned due to ${alert.attack_type} attack`,
        ban_duration: 'PERMANENT',
      });
      await handleUpdateAlertStatus(alert.alert_id, 'BANNED');
      await loadDashboardData();
      adminToasts.userBanned();
    } catch (error: any) {
      console.error('Failed to ban:', error);
      alert(error.message || 'Failed to ban user/IP');
    }
  };

  // Handle export alerts
  const handleExportAlerts = async (format: 'json' | 'csv') => {
    try {
      const blob = await exportAlerts(format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `alerts_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      adminToasts.dataExported(format);
    } catch (error) {
      console.error('Failed to export:', error);
      alert('Failed to export alerts');
    }
  };

  // Handle clear all alerts
  const handleClearAllAlerts = async () => {
    if (!confirm('Are you sure you want to clear ALL alerts? This action cannot be undone.')) {
      return;
    }

    try {
      const result = await clearAllAlerts();
      if (result.success) {
        await loadAlerts();
        adminToasts.alertUpdated();
      } else {
        alert(result.message || 'Failed to clear alerts');
      }
    } catch (error: any) {
      console.error('Failed to clear alerts:', error);
      alert(error.message || 'Failed to clear alerts');
    }
  };

  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect to login
  }

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-border pb-4">
          <div>
            <div>
              <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
                <Shield className="text-error" size={32} />
                Security Admin Dashboard
              </h1>
              <p className="text-foreground-secondary mt-1">
                Welcome, {adminUser?.username || 'Admin'} • Monitor and manage security alerts
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleLogout}
              className="px-4 py-2 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors flex items-center gap-2"
            >
              <Lock size={16} />
              Logout
            </button>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                autoRefresh
                  ? 'bg-primary/10 border-primary text-primary'
                  : 'bg-background-elevated border-border text-foreground-secondary'
              }`}
            >
              {autoRefresh ? <RefreshCw className="animate-spin" size={16} /> : <RefreshCw size={16} />}
              Auto-refresh
            </button>
            {newAlertsCount > 0 && (
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-error/10 border border-error/20 text-error">
                <Bell size={16} />
                <span className="font-bold">{newAlertsCount}</span>
                <span>New Alerts</span>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-border">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'overview'
                ? 'border-primary text-primary'
                : 'border-transparent text-foreground-secondary hover:text-foreground'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 relative ${
              activeTab === 'alerts'
                ? 'border-primary text-primary'
                : 'border-transparent text-foreground-secondary hover:text-foreground'
            }`}
          >
            Alerts
            {newAlertsCount > 0 && (
              <span className="absolute top-1 right-1 bg-error text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {newAlertsCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'users'
                ? 'border-primary text-primary'
                : 'border-transparent text-foreground-secondary hover:text-foreground'
            }`}
          >
            Users
          </button>
          <button
            onClick={() => setActiveTab('web-requests')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'web-requests'
                ? 'border-primary text-primary'
                : 'border-transparent text-foreground-secondary hover:text-foreground'
            }`}
          >
            Web Requests
          </button>
          <button
            onClick={() => setActiveTab('soar')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'soar'
                ? 'border-primary text-primary'
                : 'border-transparent text-foreground-secondary hover:text-foreground'
            }`}
          >
            SOAR
          </button>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                icon={<Users size={24} />}
                label="Total Users"
                value={stats.total_users.toLocaleString()}
                color="text-primary"
              />
              <StatCard
                icon={<AlertTriangle size={24} />}
                label="Alerts (24h)"
                value={stats.total_alerts_24h.toLocaleString()}
                color="text-error"
                badge={stats.critical_alerts_24h > 0 ? `${stats.critical_alerts_24h} critical` : undefined}
              />
              <StatCard
                icon={<Ban size={24} />}
                label="Banned"
                value={`${stats.banned_users} users, ${stats.banned_ips} IPs`}
                color="text-warning"
              />
              <StatCard
                icon={<Server size={24} />}
                label="System Health"
                value={stats.system_health}
                color={
                  stats.system_health === 'HEALTHY'
                    ? 'text-success'
                    : stats.system_health === 'CRITICAL'
                    ? 'text-error'
                    : 'text-warning'
                }
              />
            </div>

            {/* Charts */}
            {graphData && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Alerts Timeline */}
                <div className="bg-background-elevated p-6 rounded-xl border border-border">
                  <h3 className="text-lg font-bold text-foreground mb-4">Alerts Timeline (7 days)</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={graphData.alerts_timeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-20" />
                      <XAxis dataKey="date" stroke="currentColor" className="text-xs" />
                      <YAxis stroke="currentColor" className="text-xs" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'var(--background-elevated)',
                          border: '1px solid var(--border)',
                          borderRadius: '8px',
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="count"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={{ fill: '#3b82f6', r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Alerts by Type */}
                <div className="bg-background-elevated p-6 rounded-xl border border-border">
                  <h3 className="text-lg font-bold text-foreground mb-4">Alerts by Type</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={Object.entries(graphData.alerts_by_type).map(([name, value]) => ({ name, value }))}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {Object.entries(graphData.alerts_by_type).map((_, index) => (
                          <Cell key={`cell-${index}`} fill={Object.values(SEVERITY_COLORS)[index % 4]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Alerts by Severity */}
                <div className="bg-background-elevated p-6 rounded-xl border border-border">
                  <h3 className="text-lg font-bold text-foreground mb-4">Alerts by Severity</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={Object.entries(graphData.alerts_by_severity).map(([name, value]) => ({ name, value }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-20" />
                      <XAxis dataKey="name" stroke="currentColor" className="text-xs" />
                      <YAxis stroke="currentColor" className="text-xs" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'var(--background-elevated)',
                          border: '1px solid var(--border)',
                          borderRadius: '8px',
                        }}
                      />
                      <Bar dataKey="value" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Top Attacking IPs */}
                <div className="bg-background-elevated p-6 rounded-xl border border-border">
                  <h3 className="text-lg font-bold text-foreground mb-4">Top Attacking IPs</h3>
                  <div className="space-y-2">
                    {graphData.top_attacking_ips.slice(0, 5).map((item, index) => (
                      <div key={index} className="flex justify-between items-center p-2 rounded bg-background">
                        <span className="font-mono text-sm text-foreground-secondary">{item.ip}</span>
                        <span className="font-bold text-foreground">{item.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <div className="space-y-4">
            {/* Filters */}
            <div className="bg-background-elevated p-4 rounded-xl border border-border">
              <div className="flex justify-between items-center mb-4">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:border-primary transition-colors"
                >
                  <Filter size={16} />
                  Filters
                </button>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExportAlerts('json')}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:border-primary transition-colors"
                  >
                    <Download size={16} />
                    Export JSON
                  </button>
                  <button
                    onClick={() => handleExportAlerts('csv')}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:border-primary transition-colors"
                  >
                    <Download size={16} />
                    Export CSV
                  </button>
                  <button
                    onClick={handleClearAllAlerts}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors"
                  >
                    <XCircle size={16} />
                    Clear All Alerts
                  </button>
                </div>
              </div>

              {showFilters && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <select
                    value={filters.severity || ''}
                    onChange={(e) => setFilters({ ...filters, severity: e.target.value || undefined })}
                    className="px-4 py-2 rounded-lg border border-border bg-background text-foreground"
                  >
                    <option value="">All Severities</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                  <select
                    value={filters.attack_type || ''}
                    onChange={(e) => setFilters({ ...filters, attack_type: e.target.value || undefined })}
                    className="px-4 py-2 rounded-lg border border-border bg-background text-foreground"
                  >
                    <option value="">All Types</option>
                    <option value="XSS">XSS</option>
                    <option value="SQL_INJECTION">SQL Injection</option>
                    <option value="COMMAND_INJECTION">Command Injection</option>
                    <option value="BRUTE_FORCE">Brute Force</option>
                    <option value="UNAUTHORIZED_ACCESS">Unauthorized Access</option>
                    <option value="API_ABUSE">API Abuse</option>
                  </select>
                  <select
                    value={filters.status || ''}
                    onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}
                    className="px-4 py-2 rounded-lg border border-border bg-background text-foreground"
                  >
                    <option value="">All Statuses</option>
                    <option value="NEW">New</option>
                    <option value="REVIEWED">Reviewed</option>
                    <option value="BANNED">Banned</option>
                    <option value="IGNORED">Ignored</option>
                    <option value="FALSE_POSITIVE">False Positive</option>
                  </select>
                  <button
                    onClick={loadAlerts}
                    className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
                  >
                    Apply Filters
                  </button>
                </div>
              )}
            </div>

            {/* Alerts List */}
            <div className="bg-background-elevated rounded-xl border border-border overflow-hidden">
              {alertLoading ? (
                <div className="flex items-center justify-center p-12">
                  <RefreshCw className="animate-spin text-primary" size={32} />
                </div>
              ) : alerts.length === 0 ? (
                <div className="text-center p-12 text-foreground-secondary">No alerts found</div>
              ) : (
                <div className="divide-y divide-border">
                  {alerts.map((alert) => (
                    <AlertRow
                      key={alert.alert_id}
                      alert={alert}
                      onSelect={() => setSelectedAlert(alert)}
                      onUpdateStatus={handleUpdateAlertStatus}
                      onBan={handleBan}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <UsersManagementTab />
        )}

        {/* Web Requests Tab */}
        {activeTab === 'web-requests' && (
          <WebRequestsTab />
        )}

        {/* SOAR Tab */}
        {activeTab === 'soar' && (
          <SOARConfigTab />
        )}

        {/* Alert Detail Modal */}
        {selectedAlert && (
          <AlertDetailModal
            alert={selectedAlert}
            onClose={() => setSelectedAlert(null)}
            onUpdateStatus={handleUpdateAlertStatus}
            onBan={handleBan}
          />
        )}
      </div>
    </div>
  );
};

// Stat Card Component
const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
  badge?: string;
}> = ({ icon, label, value, color, badge }) => (
  <div className="bg-background-elevated p-6 rounded-xl border border-border">
    <div className="flex items-center justify-between mb-2">
      <div className={`${color}`}>{icon}</div>
      {badge && <span className="text-xs text-foreground-secondary bg-warning/10 px-2 py-1 rounded">{badge}</span>}
    </div>
    <p className="text-sm text-foreground-secondary mb-1">{label}</p>
    <p className={`text-2xl font-bold ${color}`}>{value}</p>
  </div>
);

// Alert Row Component
const AlertRow: React.FC<{
  alert: SecurityAlert;
  onSelect: () => void;
  onUpdateStatus: (id: number, status: string) => void;
  onBan: (alert: SecurityAlert) => void;
}> = ({ alert, onSelect, onUpdateStatus, onBan }) => {
  const severityColor = SEVERITY_COLORS[alert.severity] || '#6b7280';
  const statusColor = STATUS_COLORS[alert.status] || '#6b7280';

  return (
    <div
      className="p-4 hover:bg-background-hover transition-colors cursor-pointer"
      onClick={onSelect}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 flex-1">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: severityColor }}
          />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-bold text-foreground">{alert.attack_type}</span>
              <span
                className="px-2 py-0.5 rounded text-xs font-medium"
                style={{ backgroundColor: `${severityColor}20`, color: severityColor }}
              >
                {alert.severity}
              </span>
              <span
                className="px-2 py-0.5 rounded text-xs font-medium"
                style={{ backgroundColor: `${statusColor}20`, color: statusColor }}
              >
                {alert.status}
              </span>
            </div>
            <div className="text-sm text-foreground-secondary">
              <span className="font-mono">{alert.ip_address}</span>
              {' • '}
              <span>{alert.endpoint}</span>
              {' • '}
              <span>{new Date(alert.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          {alert.status === 'NEW' && (
            <>
              <button
                onClick={() => onUpdateStatus(alert.alert_id, 'REVIEWED')}
                className="px-3 py-1.5 rounded-lg bg-success/10 text-success hover:bg-success/20 transition-colors text-sm"
              >
                Review
              </button>
              <button
                onClick={() => onBan(alert)}
                className="px-3 py-1.5 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors text-sm"
              >
                Ban
              </button>
            </>
          )}
          <Eye size={16} className="text-foreground-secondary" />
        </div>
      </div>
    </div>
  );
};

// Alert Detail Modal
const AlertDetailModal: React.FC<{
  alert: SecurityAlert;
  onClose: () => void;
  onUpdateStatus: (id: number, status: string) => void;
  onBan: (alert: SecurityAlert) => void;
}> = ({ alert, onClose, onUpdateStatus, onBan }) => {
  const severityColor = SEVERITY_COLORS[alert.severity] || '#6b7280';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-background-elevated rounded-xl border border-border max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-border">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Alert Details</h2>
              <div className="flex items-center gap-2">
                <span className="font-bold text-foreground">{alert.attack_type}</span>
                <span
                  className="px-2 py-1 rounded text-sm font-medium"
                  style={{ backgroundColor: `${severityColor}20`, color: severityColor }}
                >
                  {alert.severity}
                </span>
                <span className="text-sm text-foreground-secondary">
                  Risk Score: {alert.risk_score}/100
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-background-hover rounded-lg transition-colors"
            >
              <XCircle size={24} className="text-foreground-secondary" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <DetailRow label="IP Address" value={alert.ip_address} />
          <DetailRow label="Endpoint" value={alert.endpoint} />
          <DetailRow label="User ID" value={alert.user_id?.toString() || 'Guest'} />
          <DetailRow label="User Agent" value={alert.user_agent || 'Unknown'} />
          <DetailRow label="Status" value={alert.status} />
          <DetailRow label="Created At" value={new Date(alert.created_at).toLocaleString()} />
          {alert.payload && (
            <div>
              <label className="text-sm font-medium text-foreground-secondary mb-2 block">Payload</label>
              <pre className="p-4 rounded-lg bg-background border border-border text-xs text-foreground-secondary overflow-x-auto">
                {alert.payload}
              </pre>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-border flex justify-end gap-2">
          {alert.status === 'NEW' && (
            <>
              <button
                onClick={() => onUpdateStatus(alert.alert_id, 'REVIEWED')}
                className="px-4 py-2 rounded-lg bg-success/10 text-success hover:bg-success/20 transition-colors"
              >
                Mark as Reviewed
              </button>
              <button
                onClick={() => onUpdateStatus(alert.alert_id, 'IGNORED')}
                className="px-4 py-2 rounded-lg bg-background border border-border hover:border-primary transition-colors"
              >
                Ignore
              </button>
              <button
                onClick={() => onBan(alert)}
                className="px-4 py-2 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors"
              >
                Ban User/IP
              </button>
            </>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-background border border-border hover:border-primary transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

const DetailRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <label className="text-sm font-medium text-foreground-secondary mb-1 block">{label}</label>
    <p className="text-foreground font-mono text-sm">{value}</p>
  </div>
);

// ============================================================================
// Users Management Tab Component
// ============================================================================
const UsersManagementTab: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);

  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getAllUsers(0, 100, search || undefined);
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Auto-refresh users list
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadUsers();
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, loadUsers]);

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }

    try {
      const result = await deleteUser(userId);
      if (result.success) {
        await loadUsers();
        adminToasts.alertUpdated();
      } else {
        alert(result.message || 'Failed to delete user');
      }
    } catch (error: any) {
      console.error('Failed to delete user:', error);
      alert(error.message || 'Failed to delete user');
    }
  };

  const handleSuspendUser = async (userId: number, isActive: boolean) => {
    try {
      await updateUser(userId, { is_active: isActive });
      await loadUsers();
      adminToasts.alertUpdated();
    } catch (error) {
      console.error('Failed to update user:', error);
      alert('Failed to update user');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-foreground">User Management</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
              autoRefresh
                ? 'bg-primary/10 border-primary text-primary'
                : 'bg-background-elevated border-border text-foreground-secondary'
            }`}
          >
            {autoRefresh ? <RefreshCw className="animate-spin" size={16} /> : <RefreshCw size={16} />}
            Auto-refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
          >
            + Create User
          </button>
        </div>
      </div>

      <div className="bg-background-elevated p-4 rounded-xl border border-border">
        <input
          type="text"
          placeholder="Search by email, username, or role..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <RefreshCw className="animate-spin text-primary" size={32} />
        </div>
      ) : (
        <div className="bg-background-elevated rounded-xl border border-border overflow-hidden">
          <div className="divide-y divide-border">
            {users.map((user) => (
              <div key={user.user_id} className="p-4 hover:bg-background-hover transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-foreground">{user.email}</span>
                      {user.username && (
                        <span className="text-sm text-foreground-secondary">({user.username})</span>
                      )}
                      <span className={`px-2 py-0.5 rounded text-xs ${user.is_active ? 'bg-success/20 text-success' : 'bg-error/20 text-error'}`}>
                        {user.is_active ? 'Active' : 'Suspended'}
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs bg-primary/20 text-primary">
                        {user.role}
                      </span>
                    </div>
                    <div className="text-sm text-foreground-secondary">
                      {user.first_name} {user.last_name} • Created: {new Date(user.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setSelectedUser(user);
                        setShowUserModal(true);
                      }}
                      className="px-3 py-1.5 rounded-lg border border-border hover:border-primary transition-colors text-sm"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleSuspendUser(user.user_id, !user.is_active)}
                      className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                        user.is_active
                          ? 'bg-warning/10 text-warning hover:bg-warning/20'
                          : 'bg-success/10 text-success hover:bg-success/20'
                      }`}
                    >
                      {user.is_active ? 'Suspend' : 'Activate'}
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.user_id)}
                      className="px-3 py-1.5 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showUserModal && selectedUser && (
        <UserDetailModal
          user={selectedUser}
          onClose={() => {
            setShowUserModal(false);
            setSelectedUser(null);
          }}
          onUpdate={loadUsers}
        />
      )}

      {showCreateModal && (
        <CreateUserModal
          onClose={() => {
            setShowCreateModal(false);
            loadUsers();
          }}
        />
      )}
    </div>
  );
};

// ============================================================================
// Web Requests Tab Component
// ============================================================================
const WebRequestsTab: React.FC = () => {
  const [requests, setRequests] = useState<WebRequest[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<WebRequestFilters>({
    skip: 0,
    limit: 50,
  });
  const [showFilters, setShowFilters] = useState(false);

  const loadRequests = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getWebRequests(filters);
      setRequests(data.results || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Failed to load web requests:', error);
      setRequests([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await exportWebRequests(format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `web_requests_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      adminToasts.dataExported(format);
    } catch (error) {
      console.error('Failed to export:', error);
      alert('Failed to export web requests');
    }
  };

  const handleClear = async () => {
    const days = prompt('Delete requests older than how many days?', '90');
    if (!days || isNaN(Number(days))) return;

    if (!confirm(`Are you sure you want to delete requests older than ${days} days?`)) {
      return;
    }

    try {
      await clearWebRequests(Number(days));
      await loadRequests();
      adminToasts.alertUpdated();
    } catch (error) {
      console.error('Failed to clear requests:', error);
      alert('Failed to clear web requests');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-foreground">Web Requests</h2>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('json')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:border-primary transition-colors"
          >
            <Download size={16} />
            Export JSON
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:border-primary transition-colors"
          >
            <Download size={16} />
            Export CSV
          </button>
          <button
            onClick={handleClear}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors"
          >
            <XCircle size={16} />
            Clear Old Requests
          </button>
        </div>
      </div>

      <div className="bg-background-elevated p-4 rounded-xl border border-border">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:border-primary transition-colors"
        >
          <Filter size={16} />
          Filters
        </button>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
            <input
              type="text"
              placeholder="IP Address"
              value={filters.ip_address || ''}
              onChange={(e) => setFilters({ ...filters, ip_address: e.target.value || undefined })}
              className="px-4 py-2 rounded-lg border border-border bg-background text-foreground"
            />
            <select
              value={filters.http_method || ''}
              onChange={(e) => setFilters({ ...filters, http_method: e.target.value || undefined })}
              className="px-4 py-2 rounded-lg border border-border bg-background text-foreground"
            >
              <option value="">All Methods</option>
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
              <option value="PATCH">PATCH</option>
            </select>
            <input
              type="text"
              placeholder="Path/Endpoint"
              value={filters.path || ''}
              onChange={(e) => setFilters({ ...filters, path: e.target.value || undefined })}
              className="px-4 py-2 rounded-lg border border-border bg-background text-foreground"
            />
            <button
              onClick={loadRequests}
              className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
            >
              Apply Filters
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <RefreshCw className="animate-spin text-primary" size={32} />
        </div>
      ) : requests.length === 0 ? (
        <div className="bg-background-elevated rounded-xl border border-border p-12 text-center">
          <p className="text-foreground-secondary">No web requests found</p>
          {total === 0 && (
            <p className="text-foreground-tertiary text-sm mt-2">
              Web requests will appear here once the middleware starts logging requests.
            </p>
          )}
        </div>
      ) : (
        <div className="bg-background-elevated rounded-xl border border-border overflow-hidden">
          <div className="p-4 border-b border-border flex justify-between items-center">
            <span className="text-sm text-foreground-secondary">
              Showing {requests.length} of {total} requests
            </span>
          </div>
          <div className="divide-y divide-border">
            {requests.map((req) => (
              <div key={req.request_id} className="p-4 hover:bg-background-hover transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-sm font-bold text-foreground">{req.http_method}</span>
                      <span className="text-foreground">{req.path}</span>
                      {req.response_status && (
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          req.response_status >= 400 ? 'bg-error/20 text-error' :
                          req.response_status >= 300 ? 'bg-warning/20 text-warning' :
                          'bg-success/20 text-success'
                        }`}>
                          {req.response_status}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-foreground-secondary">
                      <span className="font-mono">{req.ip_address}</span>
                      {' • '}
                      {req.username || 'Guest'}
                      {' • '}
                      {req.response_time_ms ? `${req.response_time_ms}ms` : 'N/A'}
                      {' • '}
                      {new Date(req.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// SOAR Configuration Tab Component
// ============================================================================
const SOARConfigTab: React.FC = () => {
  const [configs, setConfigs] = useState<SOARConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadConfigs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getSOARConfigs();
      setConfigs(data);
    } catch (error) {
      console.error('Failed to load SOAR configs:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfigs();
  }, [loadConfigs]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-foreground">SOAR Configuration</h2>
          <p className="text-foreground-secondary mt-1">Configure security event forwarding to SOAR platforms</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
        >
          + Add SOAR Platform
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <RefreshCw className="animate-spin text-primary" size={32} />
        </div>
      ) : configs.length === 0 ? (
        <div className="bg-background-elevated rounded-xl border border-border p-12 text-center">
          <p className="text-foreground-secondary mb-4">No SOAR configurations found</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
          >
            Create First Configuration
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {configs.map((config) => (
            <SOARConfigCard
              key={config.config_id}
              config={config}
              onUpdate={loadConfigs}
            />
          ))}
        </div>
      )}

      {showCreateModal && (
        <SOARConfigModal
          onClose={() => {
            setShowCreateModal(false);
            loadConfigs();
          }}
        />
      )}
    </div>
  );
};

// ============================================================================
// User Detail Modal Component
// ============================================================================
const UserDetailModal: React.FC<{
  user: User;
  onClose: () => void;
  onUpdate: () => void;
}> = ({ user, onClose, onUpdate }) => {
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [attackCount, setAttackCount] = useState(0);
  const [isSuspended, setIsSuspended] = useState(false);
  const [isBanned, setIsBanned] = useState(false);

  useEffect(() => {
    const loadActivity = async () => {
      try {
        const data = await getUserActivity(user.user_id);
        if (data && typeof data === 'object' && 'activity' in data) {
          setActivity(data.activity || []);
          setAttackCount(data.attack_count || 0);
          setIsSuspended(data.is_suspended || false);
          setIsBanned(data.is_banned || false);
        } else {
          // Backward compatibility - if it's an array
          setActivity(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        console.error('Failed to load activity:', error);
      } finally {
        setLoading(false);
      }
    };
    loadActivity();
  }, [user.user_id]);

  const handleResetPassword = async () => {
    const newPassword = prompt('Enter new password:');
    if (!newPassword) return;

    try {
      await resetUserPassword(user.user_id, newPassword);
      alert('Password reset successfully');
    } catch (error) {
      console.error('Failed to reset password:', error);
      alert('Failed to reset password');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-background-elevated rounded-xl border border-border max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-border">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-foreground mb-2">User Details</h2>
              <p className="text-foreground-secondary">{user.email}</p>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-background-hover rounded-lg">
              <XCircle size={24} className="text-foreground-secondary" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <DetailRow label="User ID" value={user.user_id.toString()} />
          <DetailRow label="Email" value={user.email} />
          <DetailRow label="Username" value={user.username || 'N/A'} />
          <DetailRow label="Name" value={`${user.first_name || ''} ${user.last_name || ''}`.trim() || 'N/A'} />
          <DetailRow label="Role" value={user.role} />
          <DetailRow label="Status" value={user.is_active ? 'Active' : 'Suspended'} />
          <DetailRow label="Email Verified" value={user.is_email_verified ? 'Yes' : 'No'} />
          <DetailRow label="Created At" value={new Date(user.created_at).toLocaleString()} />

          {(attackCount > 0 || isSuspended || isBanned) && (
            <div className="pt-4 border-t border-border">
              <h3 className="font-bold text-foreground mb-2">Security Status</h3>
              <div className="space-y-2">
                <div className="p-3 rounded-lg bg-warning/10 border border-warning/20">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">Attack Attempts</span>
                    <span className="text-lg font-bold text-warning">{attackCount}</span>
                  </div>
                  {isBanned && (
                    <p className="text-xs text-error mt-1">User is banned (10+ attacks)</p>
                  )}
                  {isSuspended && !isBanned && (
                    <p className="text-xs text-warning mt-1">User is suspended (2+ attacks)</p>
                  )}
                  {attackCount >= 2 && attackCount < 10 && (
                    <p className="text-xs text-foreground-secondary mt-1">
                      {10 - attackCount} more attacks until permanent ban
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-border">
            <h3 className="font-bold text-foreground mb-2">Activity Log</h3>
            {loading ? (
              <RefreshCw className="animate-spin text-primary" size={20} />
            ) : activity.length === 0 ? (
              <p className="text-foreground-secondary">No activity found</p>
            ) : (
              <div className="space-y-2">
                {activity.map((act, idx) => (
                  <div key={idx} className="p-2 rounded bg-background text-sm">
                    <div className="font-medium">{act.activity_type}</div>
                    <div className="text-foreground-secondary text-xs">{new Date(act.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="p-6 border-t border-border flex justify-end gap-2">
          <button
            onClick={handleResetPassword}
            className="px-4 py-2 rounded-lg bg-warning/10 text-warning hover:bg-warning/20 transition-colors"
          >
            Reset Password
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-background border border-border hover:border-primary transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Create User Modal Component
// ============================================================================
// ============================================================================
// SOAR Config Card Component
// ============================================================================
const SOARConfigCard: React.FC<{
  config: SOARConfig;
  onUpdate: () => void;
}> = ({ config, onUpdate }) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    setTesting(true);
    try {
      const result = await testSOARConnection(config.config_id);
      if (result.success) {
        alert('Connection test successful!');
      } else {
        alert('Connection test failed: ' + result.message);
      }
    } catch (error: any) {
      alert('Connection test failed: ' + (error.message || 'Unknown error'));
    } finally {
      setTesting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete "${config.platform_name}"?`)) {
      return;
    }

    try {
      await deleteSOARConfig(config.config_id);
      onUpdate();
      adminToasts.alertUpdated();
    } catch (error: any) {
      alert('Failed to delete config: ' + (error.message || 'Unknown error'));
    }
  };

  return (
    <>
      <div className="bg-background-elevated p-6 rounded-xl border border-border">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-bold text-foreground">{config.platform_name}</h3>
            <p className="text-sm text-foreground-secondary font-mono break-all">{config.endpoint_url}</p>
          </div>
          <span className={`px-2 py-1 rounded text-xs ${config.is_enabled ? 'bg-success/20 text-success' : 'bg-error/20 text-error'}`}>
            {config.is_enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
        <div className="space-y-2 text-sm mb-4">
          <div>Event Types: {config.event_types.length} configured</div>
          <div>Severity Filter: {config.severity_filter.join(', ') || 'None'}</div>
          <div>Retry Count: {config.retry_count}</div>
          <div>Timeout: {config.timeout_seconds}s</div>
        </div>
        <div className="flex gap-2 mt-4">
          <button
            onClick={handleTest}
            disabled={testing}
            className="flex-1 px-3 py-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors text-sm disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button
            onClick={() => setShowEditModal(true)}
            className="px-3 py-2 rounded-lg border border-border hover:border-primary transition-colors text-sm"
          >
            Edit
          </button>
          <button
            onClick={handleDelete}
            className="px-3 py-2 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors text-sm"
          >
            Delete
          </button>
        </div>
      </div>

      {showEditModal && (
        <SOARConfigModal
          config={config}
          onClose={() => {
            setShowEditModal(false);
            onUpdate();
          }}
        />
      )}
    </>
  );
};

// ============================================================================
// SOAR Config Modal Component
// ============================================================================
const SOARConfigModal: React.FC<{
  config?: SOARConfig;
  onClose: () => void;
}> = ({ config, onClose }) => {
  const [formData, setFormData] = useState({
    platform_name: config?.platform_name || '',
    endpoint_url: config?.endpoint_url || '',
    api_key: config?.api_key || '',
    is_enabled: config?.is_enabled ?? false,
    event_types: config?.event_types || [],
    severity_filter: config?.severity_filter || ['CRITICAL', 'HIGH'],
    retry_count: config?.retry_count || 3,
    timeout_seconds: config?.timeout_seconds || 30,
    verify_ssl: config?.verify_ssl ?? true,
    custom_headers: config?.custom_headers || {},
  });

  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const eventTypeOptions = [
    'login_attempt',
    'failed_login',
    'security_alert',
    'user_banned',
    'ip_banned',
    'suspicious_activity',
    'system_error',
    'admin_action',
  ];

  const severityOptions = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.platform_name.trim()) {
      newErrors.platform_name = 'Platform name is required';
    }
    if (!formData.endpoint_url.trim()) {
      newErrors.endpoint_url = 'Endpoint URL is required';
    } else if (!formData.endpoint_url.startsWith('http://') && !formData.endpoint_url.startsWith('https://')) {
      newErrors.endpoint_url = 'URL must start with http:// or https://';
    }
    if (!formData.api_key.trim()) {
      newErrors.api_key = 'API key is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    try {
      if (config) {
        await updateSOARConfig(config.config_id, formData);
      } else {
        await createSOARConfig(formData);
      }
      onClose();
      adminToasts.alertUpdated();
    } catch (error: any) {
      alert('Failed to save config: ' + (error.message || 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  const toggleEventType = (type: string) => {
    setFormData({
      ...formData,
      event_types: formData.event_types.includes(type)
        ? formData.event_types.filter(t => t !== type)
        : [...formData.event_types, type],
    });
  };

  const toggleSeverity = (severity: string) => {
    setFormData({
      ...formData,
      severity_filter: formData.severity_filter.includes(severity)
        ? formData.severity_filter.filter(s => s !== severity)
        : [...formData.severity_filter, severity],
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-background-elevated rounded-xl border border-border max-w-3xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-border">
          <div className="flex justify-between items-start">
            <h3 className="text-xl font-bold text-foreground">
              {config ? 'Edit SOAR Configuration' : 'Create SOAR Configuration'}
            </h3>
            <button onClick={onClose} className="p-2 hover:bg-background-hover rounded-lg">
              <XCircle size={24} className="text-foreground-secondary" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground-secondary mb-1">
              Platform Name *
            </label>
            <input
              type="text"
              value={formData.platform_name}
              onChange={(e) => setFormData({ ...formData, platform_name: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg border bg-background text-foreground ${
                errors.platform_name ? 'border-error' : 'border-border'
              }`}
              placeholder="e.g., Splunk SOAR, Cortex XSOAR"
            />
            {errors.platform_name && (
              <p className="text-error text-xs mt-1">{errors.platform_name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground-secondary mb-1">
              Endpoint URL *
            </label>
            <input
              type="url"
              value={formData.endpoint_url}
              onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg border bg-background text-foreground ${
                errors.endpoint_url ? 'border-error' : 'border-border'
              }`}
              placeholder="https://soar.example.com/api/events"
            />
            {errors.endpoint_url && (
              <p className="text-error text-xs mt-1">{errors.endpoint_url}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground-secondary mb-1">
              API Key *
            </label>
            <input
              type="password"
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg border bg-background text-foreground ${
                errors.api_key ? 'border-error' : 'border-border'
              }`}
              placeholder="Enter API key"
            />
            {errors.api_key && (
              <p className="text-error text-xs mt-1">{errors.api_key}</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_enabled"
              checked={formData.is_enabled}
              onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="is_enabled" className="text-sm text-foreground-secondary">
              Enable this configuration
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground-secondary mb-2">
              Event Types to Forward
            </label>
            <div className="grid grid-cols-2 gap-2">
              {eventTypeOptions.map((type) => (
                <label key={type} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.event_types.includes(type)}
                    onChange={() => toggleEventType(type)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-foreground">{type.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground-secondary mb-2">
              Severity Filter
            </label>
            <div className="flex gap-2 flex-wrap">
              {severityOptions.map((severity) => (
                <label key={severity} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.severity_filter.includes(severity)}
                    onChange={() => toggleSeverity(severity)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-foreground">{severity}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground-secondary mb-1">
                Retry Count
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={formData.retry_count}
                onChange={(e) => setFormData({ ...formData, retry_count: parseInt(e.target.value) || 3 })}
                className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground-secondary mb-1">
                Timeout (seconds)
              </label>
              <input
                type="number"
                min="5"
                max="300"
                value={formData.timeout_seconds}
                onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) || 30 })}
                className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="verify_ssl"
              checked={formData.verify_ssl}
              onChange={(e) => setFormData({ ...formData, verify_ssl: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="verify_ssl" className="text-sm text-foreground-secondary">
              Verify SSL certificates
            </label>
          </div>

          <div className="flex gap-2 pt-4 border-t border-border">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : config ? 'Update' : 'Create'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-background border border-border hover:border-primary transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ============================================================================
// Create User Modal Component
// ============================================================================
const CreateUserModal: React.FC<{
  onClose: () => void;
}> = ({ onClose }) => {
  const [formData, setFormData] = useState<UserCreateRequest>({
    email: '',
    password: '',
    username: '',
    first_name: '',
    last_name: '',
    role: 'BUYER',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createUser(formData);
      onClose();
      adminToasts.alertUpdated();
    } catch (error: any) {
      alert(error.message || 'Failed to create user');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-background-elevated rounded-xl border border-border max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold text-foreground mb-4">Create User</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
          />
          <input
            type="password"
            placeholder="Password"
            required
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
          />
          <input
            type="text"
            placeholder="Username (optional)"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
          />
          <input
            type="text"
            placeholder="First Name (optional)"
            value={formData.first_name}
            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
          />
          <input
            type="text"
            placeholder="Last Name (optional)"
            value={formData.last_name}
            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
          />
          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground"
          >
            <option value="BUYER">BUYER</option>
            <option value="ORGANIZER">ORGANIZER</option>
            <option value="ADMIN">ADMIN</option>
            <option value="SCANNER">SCANNER</option>
            <option value="RESELLER">RESELLER</option>
          </select>
          <div className="flex gap-2">
            <button
              type="submit"
              className="flex-1 px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
            >
              Create User
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-background border border-border hover:border-primary transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

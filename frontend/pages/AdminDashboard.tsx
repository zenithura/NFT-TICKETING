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
  type SecurityAlert,
  type AdminStats,
  type GraphData,
  type AlertFilters,
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

type TabType = 'overview' | 'alerts' | 'users';

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
          navigate('/admin/login', { replace: true });
          return;
        }
        const user = await getAdminUser();
        setAdminUser(user.admin);
        setIsAuthenticated(true);
      } catch (error) {
        navigate('/admin/login', { replace: true });
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
      navigate('/admin/login', { replace: true });
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/admin/login', { replace: true });
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
      setAlerts(alertsData);
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
      setAlerts(alertsData);
      
      // Count new alerts
      const newCount = alertsData.filter(a => a.status === 'NEW').length;
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

  // Handle export
  const handleExport = async (format: 'json' | 'csv') => {
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
          <button
            onClick={handleLogout}
            className="px-4 py-2 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors flex items-center gap-2"
          >
            <Lock size={16} />
            Logout
          </button>
          <div className="flex items-center gap-4">
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
          <div className="bg-background-elevated rounded-xl border border-border p-6">
            <p className="text-foreground-secondary">User management coming soon...</p>
          </div>
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

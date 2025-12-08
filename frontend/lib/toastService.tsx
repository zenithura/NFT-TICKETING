/**
 * Unified Toast Service
 * Centralized toast notification system for consistent messaging across the app
 */

import React from 'react';
import toast from 'react-hot-toast';
import { CheckCircle2, XCircle, Info, AlertCircle } from 'lucide-react';

/**
 * Toast configuration
 */
const TOAST_CONFIG = {
  duration: 3500, // 3.5 seconds (between 3-4 seconds as requested)
  position: 'top-right' as const,
  style: {
    borderRadius: '12px',
    background: 'var(--color-background-elevated)',
    color: 'var(--color-foreground)',
    border: '1px solid var(--color-border)',
    padding: '12px 16px',
  },
};

/**
 * Show success toast
 */
export const showSuccessToast = (message: string): void => {
  toast.success(
    (t) => (
      <div className="flex items-center gap-3">
        <CheckCircle2 className="text-success flex-shrink-0" size={20} />
        <span className="font-medium">{message}</span>
      </div>
    ),
    {
      ...TOAST_CONFIG,
      icon: undefined, // Use custom icon in content
    }
  );
};

/**
 * Show error toast
 */
export const showErrorToast = (message: string): void => {
  toast.error(
    (t) => (
      <div className="flex items-center gap-3">
        <XCircle className="text-error flex-shrink-0" size={20} />
        <span className="font-medium">{message}</span>
      </div>
    ),
    {
      ...TOAST_CONFIG,
      duration: 4000, // Errors stay a bit longer
      icon: undefined,
    }
  );
};

/**
 * Show info toast
 */
export const showInfoToast = (message: string): void => {
  toast(
    (t) => (
      <div className="flex items-center gap-3">
        <Info className="text-primary flex-shrink-0" size={20} />
        <span className="font-medium">{message}</span>
      </div>
    ),
    {
      ...TOAST_CONFIG,
      icon: undefined,
    }
  );
};

/**
 * Show warning toast
 */
export const showWarningToast = (message: string): void => {
  toast(
    (t) => (
      <div className="flex items-center gap-3">
        <AlertCircle className="text-warning flex-shrink-0" size={20} />
        <span className="font-medium">{message}</span>
      </div>
    ),
    {
      ...TOAST_CONFIG,
      icon: undefined,
    }
  );
};

/**
 * Authentication-specific toasts
 */
export const authToasts = {
  loginSuccess: () => showSuccessToast('Successfully logged in'),
  registerSuccess: () => showSuccessToast('Account created successfully'),
  logoutSuccess: () => showSuccessToast('Successfully logged out'),
  profileUpdated: () => showSuccessToast('Profile updated successfully'),
  passwordReset: () => showSuccessToast('Password reset successfully'),
  emailSent: () => showSuccessToast('Email sent successfully'),
};

/**
 * Wallet-specific toasts
 */
export const walletToasts = {
  connected: () => showSuccessToast('Wallet connected successfully'),
  disconnected: () => showSuccessToast('Wallet disconnected successfully'),
  connectionFailed: (message?: string) => showErrorToast(message || 'Failed to connect wallet'),
};

/**
 * Language-specific toasts
 */
export const languageToasts = {
  changed: (languageName: string) => showSuccessToast(`Language changed to ${languageName}`),
};

/**
 * Admin-specific toasts
 */
export const adminToasts = {
  loginSuccess: () => showSuccessToast('Admin login successful'),
  logoutSuccess: () => showSuccessToast('Admin logout successful'),
  actionSuccess: (action: string) => showSuccessToast(`${action} completed successfully`),
  userBanned: () => showSuccessToast('User/IP banned successfully'),
  userUnbanned: () => showSuccessToast('User/IP unbanned successfully'),
  alertUpdated: () => showSuccessToast('Alert status updated successfully'),
  dataExported: (format: string) => showSuccessToast(`Data exported as ${format.toUpperCase()} successfully`),
};

/**
 * API operation toasts
 */
export const apiToasts = {
  createSuccess: (resource: string) => showSuccessToast(`${resource} created successfully`),
  updateSuccess: (resource: string) => showSuccessToast(`${resource} updated successfully`),
  deleteSuccess: (resource: string) => showSuccessToast(`${resource} deleted successfully`),
  operationSuccess: (message: string) => showSuccessToast(message),
};


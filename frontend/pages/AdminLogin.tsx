/**
 * Admin Login Page
 * Secure admin authentication with rate limiting and security logging
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Lock, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react';
import { adminLogin, checkAdminSession } from '../services/adminAuthService';
import { adminToasts } from '../lib/toastService';

export const AdminLogin: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  // Check if admin is already logged in
  useEffect(() => {
    const checkSession = async () => {
      try {
        const isAuthenticated = await checkAdminSession();
        if (isAuthenticated) {
          // Redirect to dashboard if already logged in
          const from = (location.state as any)?.from?.pathname || '/secure-admin/dashboard';
          navigate(from, { replace: true });
        }
      } catch (error) {
        // Not authenticated, stay on login page
      } finally {
        setIsCheckingSession(false);
      }
    };

    checkSession();
  }, [navigate, location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    const trimmedUsername = username.trim();
    const trimmedPassword = password.trim();

    if (!trimmedUsername || !trimmedPassword) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);

    try {
      const loginResponse = await adminLogin(trimmedUsername, trimmedPassword);
      console.log('Login response:', loginResponse);
      
      // Wait a bit longer for cookie to be set and propagated
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Double-check session before redirect - retry up to 3 times
      let sessionValid = false;
      for (let i = 0; i < 3; i++) {
        sessionValid = await checkAdminSession();
        if (sessionValid) break;
        // Wait a bit longer between retries
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      if (!sessionValid) {
        console.error('Session validation failed after login');
        setError('Session could not be established. The cookie may not be set due to cross-origin restrictions. Please ensure both frontend and backend are on the same origin, or use a proxy.');
        return;
      }
      
      // Show success toast
      adminToasts.loginSuccess();
      
      // Redirect to dashboard on success
      const from = (location.state as any)?.from?.pathname || '/secure-admin/dashboard';
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error('Login error:', error);
      setError(error.message || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleSubmit(e as any);
    }
  };

  if (isCheckingSession) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'transparent' }}>
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'transparent' }}>
      <div className="w-full max-w-md">
        {/* Login Card */}
        <div className="bg-background-elevated rounded-2xl border border-border shadow-xl p-8 space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="flex justify-center">
              <div className="p-3 rounded-full bg-primary/10 border border-primary/20">
                <Lock className="text-primary" size={32} />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-foreground">Admin Login</h1>
            <p className="text-sm text-foreground-secondary">
              Enter your credentials to access the admin dashboard
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-foreground mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                placeholder="Enter username"
                autoComplete="username"
                disabled={loading}
                autoFocus
              />
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="w-full px-4 py-3 pr-12 rounded-lg border border-border bg-background text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                  placeholder="Enter password"
                  autoComplete="current-password"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground-tertiary hover:text-foreground transition-colors"
                  disabled={loading}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            {/* Login Button */}
            <button
              type="submit"
              disabled={loading || !username.trim() || !password.trim()}
              className="w-full py-3 rounded-lg bg-primary text-white font-medium hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span>Logging in...</span>
                </>
              ) : (
                <span>Login</span>
              )}
            </button>
          </form>

          {/* Security Notice */}
          <div className="pt-4 border-t border-border">
            <p className="text-xs text-foreground-tertiary text-center">
              All login attempts are logged for security purposes
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-xs text-foreground-tertiary">
            © 2025 NFTix Platform. Admin Access Only.
          </p>
        </div>
      </div>
    </div>
  );
};


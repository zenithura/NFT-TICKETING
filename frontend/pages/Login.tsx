// File header: User login page with email and password authentication.
// Provides form validation, error handling, and redirects to dashboard on success.

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../services/authContext';
import { Mail, Lock, AlertCircle, Loader2 } from 'lucide-react';
import { authToasts, showErrorToast } from '../lib/toastService';
import { cn } from '../lib/utils';

export const Login: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  // Purpose: Validate email format.
  // Returns: True if valid, False otherwise.
  // Side effects: Updates errors state.
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setErrors(prev => ({ ...prev, email: t('auth.errors.invalidEmail') }));
      return false;
    }
    setErrors(prev => ({ ...prev, email: undefined }));
    return true;
  };

  // Purpose: Validate password is not empty.
  // Returns: True if valid, False otherwise.
  // Side effects: Updates errors state.
  const validatePassword = (password: string): boolean => {
    if (!password || password.length === 0) {
      setErrors(prev => ({ ...prev, password: t('auth.errors.passwordRequired') }));
      return false;
    }
    setErrors(prev => ({ ...prev, password: undefined }));
    return true;
  };

  // Purpose: Handle form submission and login.
  // Side effects: Validates form, calls login API, handles errors, redirects on success.
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear previous errors
    setErrors({});
    
    // Validate inputs
    const isEmailValid = validateEmail(email);
    const isPasswordValid = validatePassword(password);
    
    if (!isEmailValid || !isPasswordValid) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      await login({ email, password });
      authToasts.loginSuccess();
      navigate('/dashboard');
    } catch (error: any) {
      const errorMessage = error.message || t('auth.errors.loginFailed');
      showErrorToast(errorMessage);
      
      // Handle specific error cases
      if (errorMessage.includes('locked')) {
        setErrors({ email: errorMessage });
      } else if (errorMessage.includes('Invalid')) {
        setErrors({ email: errorMessage, password: errorMessage });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ background: 'transparent' }}>
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t('auth.login.title')}</h1>
          <p className="text-foreground-secondary">{t('auth.login.subtitle')}</p>
        </div>

        {/* Login Form */}
        <div className="bg-background-elevated rounded-xl border border-border p-6 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                {t('auth.email')}
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (errors.email) validateEmail(e.target.value);
                  }}
                  className={cn(
                    "w-full pl-10 pr-4 py-2.5 bg-background border rounded-lg",
                    "text-foreground placeholder-foreground-tertiary",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                    errors.email ? "border-error" : "border-border"
                  )}
                  placeholder={t('auth.emailPlaceholder')}
                  disabled={isLoading}
                  autoComplete="email"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-error flex items-center gap-1">
                  <AlertCircle size={14} />
                  {errors.email}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                {t('auth.password')}
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (errors.password) validatePassword(e.target.value);
                  }}
                  className={cn(
                    "w-full pl-10 pr-4 py-2.5 bg-background border rounded-lg",
                    "text-foreground placeholder-foreground-tertiary",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                    errors.password ? "border-error" : "border-border"
                  )}
                  placeholder={t('auth.passwordPlaceholder')}
                  disabled={isLoading}
                  autoComplete="current-password"
                />
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-error flex items-center gap-1">
                  <AlertCircle size={14} />
                  {errors.password}
                </p>
              )}
            </div>

            {/* Forgot Password Link */}
            <div className="flex justify-end">
              <Link
                to="/forgot-password"
                className="text-sm text-primary hover:text-primary/80 transition-colors"
              >
                {t('auth.forgotPassword')}
              </Link>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                "w-full py-2.5 px-4 rounded-lg font-medium transition-colors",
                "bg-primary text-primary-foreground",
                "hover:bg-primary/90",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "flex items-center justify-center gap-2"
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  {t('auth.loggingIn')}
                </>
              ) : (
                t('auth.loginButton')
              )}
            </button>
          </form>

          {/* Register Link */}
          <div className="mt-6 text-center text-sm text-foreground-secondary">
            <span>{t('auth.noAccount')} </span>
            <Link to="/register" className="text-primary hover:text-primary/80 font-medium">
              {t('auth.registerLink')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};


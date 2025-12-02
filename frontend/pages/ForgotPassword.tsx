// File header: Forgot password page for requesting password reset email.
// Provides email input and sends reset link to user's email.

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { forgotPassword } from '../services/authService';
import toast from 'react-hot-toast';
import { cn } from '../lib/utils';

export const ForgotPassword: React.FC = () => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  // Purpose: Validate email format.
  // Returns: True if valid, False otherwise.
  // Side effects: Updates error state.
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError(t('auth.errors.invalidEmail'));
      return false;
    }
    setError('');
    return true;
  };

  // Purpose: Handle form submission and send reset email.
  // Side effects: Validates email, calls API, shows success/error messages.
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!validateEmail(email)) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      await forgotPassword(email);
      setIsSubmitted(true);
      toast.success(t('auth.forgotPasswordSuccess'));
    } catch (error: any) {
      const errorMessage = error.message || t('auth.errors.forgotPasswordFailed');
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
        <div className="w-full max-w-md">
          <div className="bg-background-elevated rounded-xl border border-border p-6 shadow-lg text-center">
            <div className="mb-4 flex justify-center">
              <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center">
                <CheckCircle2 className="text-success" size={32} />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-2">{t('auth.forgotPassword.checkEmail')}</h1>
            <p className="text-foreground-secondary mb-6">{t('auth.forgotPassword.emailSent', { email })}</p>
            <Link
              to="/login"
              className="inline-block px-6 py-2.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
            >
              {t('auth.backToLogin')}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t('auth.forgotPassword.title')}</h1>
          <p className="text-foreground-secondary">{t('auth.forgotPassword.subtitle')}</p>
        </div>

        {/* Form */}
        <div className="bg-background-elevated rounded-xl border border-border p-6 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-4">
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
                    if (error) validateEmail(e.target.value);
                  }}
                  className={cn(
                    "w-full pl-10 pr-4 py-2.5 bg-background border rounded-lg",
                    "text-foreground placeholder-foreground-tertiary",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                    error ? "border-error" : "border-border"
                  )}
                  placeholder={t('auth.emailPlaceholder')}
                  disabled={isLoading}
                  required
                  autoComplete="email"
                />
              </div>
              {error && (
                <p className="mt-1 text-sm text-error flex items-center gap-1">
                  <AlertCircle size={14} />
                  {error}
                </p>
              )}
            </div>

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
                  {t('auth.sending')}
                </>
              ) : (
                t('auth.sendResetLink')
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-foreground-secondary">
            <Link to="/login" className="text-primary hover:text-primary/80 font-medium">
              {t('auth.backToLogin')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};


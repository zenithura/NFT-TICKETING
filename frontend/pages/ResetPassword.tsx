// File header: Reset password page for setting new password using reset token.
// Validates password strength and updates user password.

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Lock, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { resetPassword } from '../services/authService';
import toast from 'react-hot-toast';
import { cn } from '../lib/utils';

export const ResetPassword: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<{ password?: string; confirmPassword?: string }>({});
  
  const token = searchParams.get('token');

  // Purpose: Validate token is present in URL.
  // Side effects: Redirects to login if token missing.
  useEffect(() => {
    if (!token) {
      toast.error(t('auth.errors.invalidResetToken'));
      navigate('/forgot-password');
    }
  }, [token, navigate, t]);

  // Purpose: Validate password strength.
  // Returns: Object with validation result and error messages.
  // Side effects: None - validation only.
  const validatePassword = (password: string): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    if (password.length < 8) {
      errors.push(t('auth.errors.passwordMinLength'));
    }
    if (!/[A-Z]/.test(password)) {
      errors.push(t('auth.errors.passwordUppercase'));
    }
    if (!/[a-z]/.test(password)) {
      errors.push(t('auth.errors.passwordLowercase'));
    }
    if (!/[0-9]/.test(password)) {
      errors.push(t('auth.errors.passwordDigit'));
    }
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push(t('auth.errors.passwordSpecial'));
    }
    
    return { valid: errors.length === 0, errors };
  };

  // Purpose: Handle form submission and reset password.
  // Side effects: Validates passwords, calls API, handles errors, redirects on success.
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token) {
      toast.error(t('auth.errors.invalidResetToken'));
      navigate('/forgot-password');
      return;
    }
    
    setErrors({});
    
    const passwordValidation = validatePassword(password);
    
    if (!passwordValidation.valid) {
      setErrors({ password: passwordValidation.errors[0] });
      return;
    }
    
    if (password !== confirmPassword) {
      setErrors({ confirmPassword: t('auth.errors.passwordMismatch') });
      return;
    }
    
    setIsLoading(true);
    
    try {
      await resetPassword(token, password);
      setIsSuccess(true);
      toast.success(t('auth.resetPasswordSuccess'));
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error: any) {
      const errorMessage = error.message || t('auth.errors.resetPasswordFailed');
      toast.error(errorMessage);
      
      if (errorMessage.includes('expired') || errorMessage.includes('Invalid')) {
        setErrors({ password: errorMessage });
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return null;
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ background: 'transparent' }}>
        <div className="w-full max-w-md">
          <div className="bg-background-elevated rounded-xl border border-border p-6 shadow-lg text-center">
            <div className="mb-4 flex justify-center">
              <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center">
                <CheckCircle2 className="text-success" size={32} />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-2">{t('auth.resetPassword.success')}</h1>
            <p className="text-foreground-secondary mb-6">{t('auth.resetPassword.redirecting')}</p>
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

  const passwordValidation = validatePassword(password);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ background: 'transparent' }}>
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t('auth.resetPassword.title')}</h1>
          <p className="text-foreground-secondary">{t('auth.resetPassword.subtitle')}</p>
        </div>

        {/* Form */}
        <div className="bg-background-elevated rounded-xl border border-border p-6 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* New Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                {t('auth.newPassword')} *
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (errors.password) {
                      const validation = validatePassword(e.target.value);
                      if (validation.valid) {
                        setErrors(prev => ({ ...prev, password: undefined }));
                      }
                    }
                  }}
                  className={cn(
                    "w-full pl-10 pr-4 py-2.5 bg-background border rounded-lg",
                    "text-foreground placeholder-foreground-tertiary",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                    errors.password ? "border-error" : "border-border"
                  )}
                  placeholder={t('auth.passwordPlaceholder')}
                  disabled={isLoading}
                  required
                  autoComplete="new-password"
                />
              </div>
              {password && (
                <div className="mt-2 space-y-1">
                  {passwordValidation.errors.map((error, idx) => (
                    <p key={idx} className="text-xs text-foreground-tertiary flex items-center gap-1">
                      <AlertCircle size={12} />
                      {error}
                    </p>
                  ))}
                  {passwordValidation.valid && (
                    <p className="text-xs text-success flex items-center gap-1">
                      <CheckCircle2 size={12} />
                      {t('auth.passwordValid')}
                    </p>
                  )}
                </div>
              )}
              {errors.password && (
                <p className="mt-1 text-sm text-error flex items-center gap-1">
                  <AlertCircle size={14} />
                  {errors.password}
                </p>
              )}
            </div>

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground mb-2">
                {t('auth.confirmPassword')} *
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (errors.confirmPassword) {
                      if (password === e.target.value) {
                        setErrors(prev => ({ ...prev, confirmPassword: undefined }));
                      }
                    }
                  }}
                  className={cn(
                    "w-full pl-10 pr-4 py-2.5 bg-background border rounded-lg",
                    "text-foreground placeholder-foreground-tertiary",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                    errors.confirmPassword ? "border-error" : "border-border"
                  )}
                  placeholder={t('auth.confirmPasswordPlaceholder')}
                  disabled={isLoading}
                  required
                  autoComplete="new-password"
                />
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-error flex items-center gap-1">
                  <AlertCircle size={14} />
                  {errors.confirmPassword}
                </p>
              )}
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
                  {t('auth.resetting')}
                </>
              ) : (
                t('auth.resetPasswordButton')
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


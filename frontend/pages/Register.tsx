// File header: User registration page with form validation and password strength requirements.
// Creates new user accounts with email verification.

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../services/authContext';
import { Mail, Lock, User, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { authToasts, showErrorToast } from '../lib/toastService';
import { cn } from '../lib/utils';

export const Register: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    username: '',
    firstName: '',
    lastName: '',
    role: 'BUYER' as 'BUYER' | 'ORGANIZER', // Only two account types available: Buyer and Organizer
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

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

  // Purpose: Handle form field changes with validation.
  // Side effects: Updates form data and validates fields.
  const handleChange = (field: string, value: string) => {
    // Use functional update to get the latest state immediately
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      
      // Clear error for this field
      if (errors[field]) {
        setErrors(prevErrors => {
          const newErrors = { ...prevErrors };
          delete newErrors[field];
          return newErrors;
        });
      }
      
      // Validate password in real-time
      if (field === 'password') {
        const validation = validatePassword(value);
        if (!validation.valid && value.length > 0) {
          setErrors(prevErrors => ({ ...prevErrors, password: validation.errors[0] }));
        } else if (validation.valid) {
          setErrors(prevErrors => {
            const newErrors = { ...prevErrors };
            delete newErrors.password;
            return newErrors;
          });
        }
      }
      
      // Validate password match using UPDATED values (not stale state)
      // CRITICAL FIX: Use 'updated' object instead of 'prev' to get the latest values
      if (field === 'confirmPassword' || field === 'password') {
        const currentPassword = field === 'password' ? value : updated.password;
        const currentConfirmPassword = field === 'confirmPassword' ? value : updated.confirmPassword;
        
        if (currentPassword && currentConfirmPassword) {
          if (currentPassword !== currentConfirmPassword) {
            setErrors(prevErrors => ({ ...prevErrors, confirmPassword: t('auth.errors.passwordMismatch') }));
          } else {
            setErrors(prevErrors => {
              const newErrors = { ...prevErrors };
              delete newErrors.confirmPassword;
              return newErrors;
            });
          }
        } else if (field === 'confirmPassword' && currentPassword && !currentConfirmPassword) {
          // Clear error if confirmPassword is cleared
          setErrors(prevErrors => {
            const newErrors = { ...prevErrors };
            delete newErrors.confirmPassword;
            return newErrors;
          });
        }
      }
      
      return updated;
    });
  };

  // Purpose: Handle form submission and registration.
  // Side effects: Validates form, calls register API, handles errors, redirects on success.
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setErrors({});
    
    // Validate all fields
    const isEmailValid = validateEmail(formData.email);
    const passwordValidation = validatePassword(formData.password);
    
    if (!isEmailValid || !passwordValidation.valid) {
      if (!passwordValidation.valid) {
        setErrors(prev => ({ ...prev, password: passwordValidation.errors[0] }));
      }
      return;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setErrors(prev => ({ ...prev, confirmPassword: t('auth.errors.passwordMismatch') }));
      return;
    }
    
    setIsLoading(true);
    
    try {
      await register({
        email: formData.email,
        password: formData.password,
        username: formData.username || undefined,
        first_name: formData.firstName || undefined,
        last_name: formData.lastName || undefined,
        role: formData.role, // Include selected role
      });
      authToasts.registerSuccess();
      navigate('/dashboard');
    } catch (error: any) {
      const errorMessage = error.message || t('auth.errors.registerFailed');
      showErrorToast(errorMessage);
      
      if (errorMessage.includes('already registered')) {
        setErrors({ email: errorMessage });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const passwordValidation = validatePassword(formData.password);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ background: 'transparent' }}>
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t('auth.register.title')}</h1>
          <p className="text-foreground-secondary">{t('auth.register.subtitle')}</p>
        </div>

        {/* Registration Form */}
        <div className="bg-background-elevated rounded-xl border border-border p-6 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                {t('auth.email')} *
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  className={cn(
                    "w-full pl-10 pr-4 py-2.5 bg-background border rounded-lg",
                    "text-foreground placeholder-foreground-tertiary",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                    errors.email ? "border-error" : "border-border"
                  )}
                  placeholder={t('auth.emailPlaceholder')}
                  disabled={isLoading}
                  required
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
                {t('auth.password')} *
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                <input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleChange('password', e.target.value)}
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
              {formData.password && (
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
                  value={formData.confirmPassword}
                  onChange={(e) => handleChange('confirmPassword', e.target.value)}
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

            {/* Optional Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-foreground mb-2">
                  {t('auth.firstName')}
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                  <input
                    id="firstName"
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => handleChange('firstName', e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-lg text-foreground placeholder-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder={t('auth.firstNamePlaceholder')}
                    disabled={isLoading}
                    autoComplete="given-name"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-foreground mb-2">
                  {t('auth.lastName')}
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                  <input
                    id="lastName"
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => handleChange('lastName', e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-lg text-foreground placeholder-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder={t('auth.lastNamePlaceholder')}
                    disabled={isLoading}
                    autoComplete="family-name"
                  />
                </div>
              </div>
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-foreground mb-2">
                {t('auth.username')}
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
                <input
                  id="username"
                  type="text"
                  value={formData.username}
                  onChange={(e) => handleChange('username', e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-lg text-foreground placeholder-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder={t('auth.usernamePlaceholder')}
                  disabled={isLoading}
                  autoComplete="username"
                />
              </div>
            </div>

            {/* Account Type Selection */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                {t('auth.accountType')} *
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleChange('role', 'BUYER')}
                  disabled={isLoading}
                  className={cn(
                    "p-4 rounded-lg border-2 transition-all",
                    "flex flex-col items-center gap-2",
                    formData.role === 'BUYER'
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-background text-foreground-secondary hover:border-border-hover"
                  )}
                >
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center",
                    formData.role === 'BUYER' ? "bg-primary text-white" : "bg-background-hover"
                  )}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                      <circle cx="9" cy="7" r="4"></circle>
                      <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                      <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                  </div>
                  <span className="font-medium">{t('auth.roleBuyer')}</span>
                  <span className="text-xs text-foreground-tertiary text-center">
                    {t('auth.roleBuyerDesc')}
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleChange('role', 'ORGANIZER')}
                  disabled={isLoading}
                  className={cn(
                    "p-4 rounded-lg border-2 transition-all",
                    "flex flex-col items-center gap-2",
                    formData.role === 'ORGANIZER'
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-background text-foreground-secondary hover:border-border-hover"
                  )}
                >
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center",
                    formData.role === 'ORGANIZER' ? "bg-primary text-white" : "bg-background-hover"
                  )}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                      <line x1="16" y1="2" x2="16" y2="6"></line>
                      <line x1="8" y1="2" x2="8" y2="6"></line>
                      <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                  </div>
                  <span className="font-medium">{t('auth.roleOrganizer')}</span>
                  <span className="text-xs text-foreground-tertiary text-center">
                    {t('auth.roleOrganizerDesc')}
                  </span>
                </button>
              </div>
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
                  {t('auth.registering')}
                </>
              ) : (
                t('auth.registerButton')
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center text-sm text-foreground-secondary">
            <span>{t('auth.haveAccount')} </span>
            <Link to="/login" className="text-primary hover:text-primary/80 font-medium">
              {t('auth.loginLink')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};


/**
 * Admin Protected Route Component
 * Redirects to admin login if not authenticated
 */

import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { checkAdminSession } from '../services/adminAuthService';
import { Loader2 } from 'lucide-react';

interface AdminProtectedRouteProps {
  children: React.ReactNode;
}

export const AdminProtectedRoute: React.FC<AdminProtectedRouteProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Add a small delay to ensure cookies are available after redirect
        await new Promise(resolve => setTimeout(resolve, 50));
        const authenticated = await checkAdminSession();
        setIsAuthenticated(authenticated);
      } catch (error) {
        console.error('Admin session check error:', error);
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, [location.pathname]); // Re-check when route changes

  if (isAuthenticated === null) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/secure-admin/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};


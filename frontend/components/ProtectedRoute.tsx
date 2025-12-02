// File header: Protected route component that requires authentication.
// Redirects unauthenticated users to login page.

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../services/authContext';

// Purpose: Props interface for ProtectedRoute component.
// Side effects: None - type definition only.
interface ProtectedRouteProps {
  children: React.ReactNode;
  requireRole?: 'admin' | 'organizer' | 'user';
}

// Purpose: Protected route wrapper that requires authentication.
// Params: children (ReactNode) — child components to render if authenticated; requireRole (optional) — required user role.
// Returns: Child components if authenticated, or Navigate to login.
// Side effects: Redirects to login if not authenticated.
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requireRole }) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  // Purpose: Show loading state while checking authentication.
  // Side effects: None - renders loading UI.
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="animate-pulse text-foreground-secondary">Loading...</div>
      </div>
    );
  }

  // Purpose: Redirect to login if not authenticated.
  // Side effects: Navigates to login page with return URL.
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Purpose: Check role-based access if required.
  // Side effects: Redirects to dashboard if role insufficient.
  if (requireRole && user) {
    const roleHierarchy: Record<string, number> = { user: 1, organizer: 2, admin: 3 };
    const userRole = user.role.toLowerCase();
    const userLevel = roleHierarchy[userRole] || 0;
    const requiredLevel = roleHierarchy[requireRole] || 0;

    if (userLevel < requiredLevel) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return <>{children}</>;
};


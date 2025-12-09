/**
 * Admin Application Component
 * Separate admin panel with non-guessable routes for enhanced security
 * Runs on port 4201 with /secure-admin paths
 */

import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { AdminProtectedRoute } from './components/AdminProtectedRoute';

// Lazy load admin pages
const AdminLogin = lazy(() => import('./pages/AdminLogin').then(m => ({ default: m.AdminLogin })));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard').then(m => ({ default: m.AdminDashboard })));

// Loading component
const PageLoader = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Loader2 className="animate-spin text-primary" size={32} />
    </div>
  );
};

/**
 * Admin Application Component
 * Provides routing for the separate admin panel
 */
const AdminApp: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen font-sans text-foreground bg-background">
      <Routes>
        {/* Admin Login - Non-guessable path */}
        <Route 
          path="/secure-admin/login" 
          element={
            <Suspense fallback={<PageLoader />}>
              <AdminLogin />
            </Suspense>
          } 
        />
        
        {/* Admin Dashboard - Protected route */}
        <Route 
          path="/secure-admin/dashboard" 
          element={
            <AdminProtectedRoute>
              <Suspense fallback={<PageLoader />}>
                <AdminDashboard />
              </Suspense>
            </AdminProtectedRoute>
          } 
        />
        
        {/* Redirect root and /secure-admin to login */}
        <Route path="/secure-admin" element={<Navigate to="/secure-admin/login" replace />} />
        <Route path="/" element={<Navigate to="/secure-admin/login" replace />} />
        
        {/* Catch all - redirect to login */}
        <Route path="*" element={<Navigate to="/secure-admin/login" replace />} />
      </Routes>
    </div>
  );
};

export default AdminApp;


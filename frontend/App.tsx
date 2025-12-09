// File header: Main React application component with routing and Web3 integration.
// Provides lazy-loaded page components and navigation structure for NFT ticketing platform.

import React, { Suspense, lazy } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Toaster } from 'react-hot-toast';
import { Web3Provider } from './services/web3Context';
import { AuthProvider } from './services/authContext';
import { ThemeProvider } from './services/themeContext';
import { Navbar } from './components/ui/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AdminProtectedRoute } from './components/AdminProtectedRoute';
import { ChatBot } from './components/ChatBot';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PerformanceOptimizer } from './components/PerformanceOptimizer';
import { ImageOptimizer } from './components/ImageOptimizer';
import { LCPOptimizer } from './components/LCPOptimizer';

// Purpose: Lazy load page components to improve initial bundle size and code splitting.
// Side effects: Components loaded on-demand when routes are accessed.
const Marketplace = lazy(() => import('./pages/Marketplace').then(m => ({ default: m.Marketplace })));
const EventDetails = lazy(() => import('./pages/EventDetails').then(m => ({ default: m.EventDetails })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const CreateEvent = lazy(() => import('./pages/CreateEvent').then(m => ({ default: m.CreateEvent })));
const Scanner = lazy(() => import('./pages/Scanner').then(m => ({ default: m.Scanner })));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const AdminLogin = lazy(() => import('./pages/AdminLogin').then(m => ({ default: m.AdminLogin })));
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Register = lazy(() => import('./pages/Register').then(m => ({ default: m.Register })));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword').then(m => ({ default: m.ForgotPassword })));
const ResetPassword = lazy(() => import('./pages/ResetPassword').then(m => ({ default: m.ResetPassword })));
const About = lazy(() => import('./pages/About').then(m => ({ default: m.About })));
const Contact = lazy(() => import('./pages/Contact').then(m => ({ default: m.Contact })));
const Features = lazy(() => import('./pages/Features').then(m => ({ default: m.Features })));
const HeroBackground = lazy(() => import('./components/3d/HeroBackground').then(m => ({ default: m.HeroBackground })));

// Purpose: Loading spinner component displayed while lazy-loaded pages are loading.
// Returns: JSX with centered loading indicator.
// Side effects: None - presentational component.
const PageLoader = () => {
  // Don't use translation here to avoid blocking on i18n
  return (
    <div className="flex items-center justify-center min-h-screen" style={{ background: 'transparent' }}>
      <div className="animate-pulse text-foreground-secondary">Loading...</div>
    </div>
  );
};

// Purpose: Fixed background placeholder to prevent layout shift during background component load.
// Returns: JSX with fixed background div.
// Side effects: Prevents cumulative layout shift (CLS) during initial render.
const BackgroundLoader = () => (
  <div className="fixed inset-0 -z-10" style={{ background: 'transparent' }} />
);

// Purpose: Defer HeroBackground loading until after initial render to improve FCP and LCP.
// Returns: JSX with deferred HeroBackground component.
// Side effects: Loads HeroBackground after a delay to not block initial paint.
const DeferredHeroBackground: React.FC = () => {
  const [shouldLoad, setShouldLoad] = React.useState(false);

  React.useEffect(() => {
    // Defer loading until after initial paint and LCP
    // Use requestIdleCallback for better performance
    const loadBackground = () => {
      if ('requestIdleCallback' in window) {
        (window as any).requestIdleCallback(() => {
          setShouldLoad(true);
        }, { timeout: 2000 });
      } else {
        // Fallback: load after LCP (typically 1-2 seconds)
        setTimeout(() => {
          setShouldLoad(true);
        }, 2000);
      }
    };

    // Wait for page to be interactive
    if (document.readyState === 'complete') {
      loadBackground();
    } else {
      window.addEventListener('load', loadBackground, { once: true });
    }
  }, []);

  if (!shouldLoad) {
    return <BackgroundLoader />;
  }

  return (
    <Suspense fallback={<BackgroundLoader />}>
      <HeroBackground />
    </Suspense>
  );
};

// Purpose: Footer component with translated copyright text.
// Returns: JSX with footer content.
// Sticks to bottom of page using flexbox layout from parent.
const Footer: React.FC = () => {
  const { t } = useTranslation();
  return (
    <footer className="border-t border-border py-12 mt-auto" style={{ background: 'transparent' }}>
      <div className="max-w-7xl mx-auto px-4 text-center text-foreground-tertiary text-sm">
        <p>{t('footer.copyright')}</p>
      </div>
    </footer>
  );
};

// Purpose: Main application component with routing, Web3 context, Auth context, and page structure.
// Returns: JSX with router, Web3 provider, Auth provider, navbar, routes, and footer.
// Side effects: Sets up React Router, provides Web3 and Auth contexts to children, renders page components.
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <PerformanceOptimizer />
      <ImageOptimizer />
      <LCPOptimizer />
      <ThemeProvider>
        <AuthProvider>
          <Web3Provider>
          <Router>
          <div className="flex flex-col min-h-screen font-sans text-foreground" style={{ background: 'transparent', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Routes>
              {/* Public Authentication Routes */}
              <Route path="/login" element={
                <Suspense fallback={<PageLoader />}>
                  <Login />
                </Suspense>
              } />
              <Route path="/register" element={
                <Suspense fallback={<PageLoader />}>
                  <Register />
                </Suspense>
              } />
              <Route path="/forgot-password" element={
                <Suspense fallback={<PageLoader />}>
                  <ForgotPassword />
                </Suspense>
              } />
              <Route path="/reset-password" element={
                <Suspense fallback={<PageLoader />}>
                  <ResetPassword />
                </Suspense>
              } />

              {/* Admin Routes - Removed: Admin panel now runs on separate port 4201 */}
              {/* Admin routes are handled by AdminApp.tsx on port 4201 with /secure-admin paths */}

              {/* Scanner Route (separate layout) */}
              <Route path="/scanner" element={
                <ProtectedRoute requireRole="user">
                  <Suspense fallback={<PageLoader />}>
                    <Scanner />
                  </Suspense>
                </ProtectedRoute>
              } />

              {/* Main Routes with Navbar */}
              {/* CRITICAL: Use flex flex-col min-h-screen to ensure footer sticks to bottom */}
              <Route path="*" element={
                <div className="flex flex-col min-h-screen" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
                  <Navbar />
                  <main className="flex-grow flex flex-col container mx-auto px-4 sm:px-6 lg:px-8 py-8" style={{ background: 'transparent', position: 'relative', zIndex: 1, flexGrow: 1, flexShrink: 0 }}>
                    <Suspense fallback={<PageLoader />}>
                      <Routes>
                        <Route path="/" element={
                          <>
                            {/* Defer HeroBackground - load after initial render */}
                            <DeferredHeroBackground />
                            <Marketplace />
                          </>
                        } />
                        <Route path="/event/:id" element={<EventDetails />} />
                        <Route path="/dashboard" element={
                          <ProtectedRoute>
                            <Dashboard />
                          </ProtectedRoute>
                        } />
                        <Route path="/create-event" element={
                          <ProtectedRoute requireRole="organizer">
                            <CreateEvent />
                          </ProtectedRoute>
                        } />
                        <Route path="/resale" element={<Navigate to="/" replace />} />
                        <Route path="/about" element={<About />} />
                        <Route path="/contact" element={<Contact />} />
                        <Route path="/features" element={<Features />} />
                      </Routes>
                    </Suspense>
                  </main>
                  <Footer />
                  <ChatBot />
                </div>
              } />
            </Routes>
          </div>
          </Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3500,
              style: {
                borderRadius: '12px',
                background: 'var(--color-background-elevated)',
                color: 'var(--color-foreground)',
                border: '1px solid var(--color-border)',
                padding: '12px 16px',
              },
            }}
          />
          </Web3Provider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;

// File header: Main React application component with routing and Web3 integration.
// Provides lazy-loaded page components and navigation structure for NFT ticketing platform.

import React, { Suspense, lazy } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Web3Provider } from './services/web3Context';
import { Navbar } from './components/ui/Navbar';

// Purpose: Lazy load page components to improve initial bundle size and code splitting.
// Side effects: Components loaded on-demand when routes are accessed.
const Marketplace = lazy(() => import('./pages/Marketplace').then(m => ({ default: m.Marketplace })));
const EventDetails = lazy(() => import('./pages/EventDetails').then(m => ({ default: m.EventDetails })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const CreateEvent = lazy(() => import('./pages/CreateEvent').then(m => ({ default: m.CreateEvent })));
const Scanner = lazy(() => import('./pages/Scanner').then(m => ({ default: m.Scanner })));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const HeroBackground = lazy(() => import('./components/3d/HeroBackground').then(m => ({ default: m.HeroBackground })));

// Purpose: Loading spinner component displayed while lazy-loaded pages are loading.
// Returns: JSX with centered loading indicator.
// Side effects: None - presentational component.
const PageLoader = () => {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="animate-pulse text-foreground-secondary">{t('common.loading')}</div>
    </div>
  );
};

// Purpose: Fixed background placeholder to prevent layout shift during background component load.
// Returns: JSX with fixed background div.
// Side effects: Prevents cumulative layout shift (CLS) during initial render.
const BackgroundLoader = () => (
  <div className="fixed inset-0 -z-10 bg-background" />
);

// Purpose: Footer component with translated copyright text.
// Returns: JSX with footer content.
const Footer: React.FC = () => {
  const { t } = useTranslation();
  return (
    <footer className="border-t border-border py-12 mt-12 bg-background">
      <div className="max-w-7xl mx-auto px-4 text-center text-foreground-tertiary text-sm">
        <p>{t('footer.copyright')}</p>
      </div>
    </footer>
  );
};

// Purpose: Main application component with routing, Web3 context, and page structure.
// Returns: JSX with router, Web3 provider, navbar, routes, and footer.
// Side effects: Sets up React Router, provides Web3 context to children, renders page components.
const App: React.FC = () => {
  return (
    <Web3Provider>
      <Router>
        <Suspense fallback={<BackgroundLoader />}>
          <HeroBackground />
        </Suspense>
        <div className="flex flex-col min-h-screen font-sans text-foreground bg-background">
          <Routes>
            <Route path="/scanner" element={
              <Suspense fallback={<PageLoader />}>
                <Scanner />
              </Suspense>
            } />

            <Route path="*" element={
              <>
                <Navbar />
                <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-background">
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route path="/" element={<Marketplace />} />
                      <Route path="/event/:id" element={<EventDetails />} />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/create-event" element={<CreateEvent />} />
                      <Route path="/admin" element={<AdminDashboard />} />
                      <Route path="/resale" element={<Navigate to="/" replace />} />
                    </Routes>
                  </Suspense>
                </main>
                <Footer />
              </>
            } />
          </Routes>
        </div>
      </Router>
    </Web3Provider>
  );
};

export default App;

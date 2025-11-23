import React, { Suspense, lazy } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Web3Provider } from './services/web3Context';
import { Navbar } from './components/ui/Navbar';

// Lazy load page components for better code splitting
const Marketplace = lazy(() => import('./pages/Marketplace').then(m => ({ default: m.Marketplace })));
const EventDetails = lazy(() => import('./pages/EventDetails').then(m => ({ default: m.EventDetails })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const CreateEvent = lazy(() => import('./pages/CreateEvent').then(m => ({ default: m.CreateEvent })));
const Scanner = lazy(() => import('./pages/Scanner').then(m => ({ default: m.Scanner })));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const HeroBackground = lazy(() => import('./components/3d/HeroBackground').then(m => ({ default: m.HeroBackground })));

// Loading component for Suspense fallback
// Loading component for Suspense fallback
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen bg-background">
    <div className="animate-pulse text-foreground-secondary">Loading...</div>
  </div>
);

// Fixed loader for background to prevent CLS
const BackgroundLoader = () => (
  <div className="fixed inset-0 -z-10 bg-background" />
);

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
                <footer className="border-t border-border py-12 mt-12 bg-background">
                  <div className="max-w-7xl mx-auto px-4 text-center text-foreground-tertiary text-sm">
                    <p>&copy; 2024 NFTix Platform. Decentralized Ticketing.</p>
                  </div>
                </footer>
              </>
            } />
          </Routes>
        </div>
      </Router>
    </Web3Provider>
  );
};

export default App;

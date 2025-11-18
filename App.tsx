import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Web3Provider } from './services/web3Context';
import { Navbar } from './components/ui/Navbar';
import { Marketplace } from './pages/Marketplace';
import { EventDetails } from './pages/EventDetails';
import { Dashboard } from './pages/Dashboard';
import { CreateEvent } from './pages/CreateEvent';
import { Scanner } from './pages/Scanner';
import { AdminDashboard } from './pages/AdminDashboard';
import { HeroBackground } from './components/3d/HeroBackground';

const App: React.FC = () => {
  return (
    <Web3Provider>
      <Router>
        <HeroBackground />
        <div className="flex flex-col min-h-screen font-sans text-foreground bg-background">
          <Routes>
            <Route path="/scanner" element={<Scanner />} />
            
            <Route path="*" element={
              <>
                <Navbar />
                <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-background">
                  <Routes>
                    <Route path="/" element={<Marketplace />} />
                    <Route path="/event/:id" element={<EventDetails />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/create-event" element={<CreateEvent />} />
                    <Route path="/admin" element={<AdminDashboard />} />
                    <Route path="/resale" element={<Navigate to="/" replace />} />
                  </Routes>
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

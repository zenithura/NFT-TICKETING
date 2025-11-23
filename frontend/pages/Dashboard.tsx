import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useWeb3 } from '../services/web3Context';
import { UserRole } from '../types';
import { Ticket, Plus, TrendingUp, Shield, DollarSign, Calendar, ArrowRight } from 'lucide-react';
import { MOCK_MY_TICKETS, MOCK_EVENTS } from '../services/mockData';
import { Skeleton } from '../components/ui/skeleton';
import { cn, formatCurrency } from '../lib/utils';

// Lazy load heavy components
const LazyChart = React.lazy(() => import('../components/LazyChart'));
// Handle named export for NFTCoinAnimation
const NFTCoinAnimation = React.lazy(() =>
  import('../components/3d/NFTCoinAnimation').then(module => ({ default: module.NFTCoinAnimation }))
);

// --- Skeleton Components ---

const TicketSkeleton = () => (
  <div className="group bg-background-elevated border border-border rounded-xl overflow-hidden">
    <div className="h-40 relative overflow-hidden bg-background-hover flex items-center justify-center">
      <div className="absolute inset-0 bg-gradient-to-t from-background-elevated to-transparent opacity-30" />
      <div className="scale-75">
        <React.Suspense fallback={<div className="w-[300px] h-[300px]" />}>
          <NFTCoinAnimation />
        </React.Suspense>
      </div>
      <div className="absolute top-3 right-3 z-10">
        <Skeleton className="h-6 w-16 rounded" />
      </div>
    </div>
    <div className="p-5">
      <Skeleton className="h-6 w-3/4 mb-2" />
      <Skeleton className="h-4 w-24 mb-4" />
      <div className="flex gap-3">
        <Skeleton className="flex-1 h-9 rounded" />
        <Skeleton className="flex-1 h-9 rounded" />
      </div>
    </div>
  </div>
);

const StatCardSkeleton = () => (
  <div className="bg-background-elevated p-6 rounded-xl border border-border">
    <div className="flex justify-between items-start mb-4">
      <Skeleton className="w-10 h-10 rounded-lg" />
      <Skeleton className="h-6 w-16 rounded" />
    </div>
    <Skeleton className="h-8 w-24 mb-2" />
    <Skeleton className="h-4 w-32 mb-2" />
    <Skeleton className="h-3 w-40" />
  </div>
);

// --- Components ---

const StatCard = ({ title, value, icon: Icon, subtext, trend }: any) => (
  <div className="bg-background-elevated p-6 rounded-xl border border-border card-hover">
    <div className="flex justify-between items-start mb-4">
      <div className="p-2 bg-background-hover rounded-lg text-foreground-secondary">
        <Icon size={20} />
      </div>
      {trend && (
        <span className="text-xs font-medium text-success bg-success/10 px-2 py-1 rounded">
          {trend}
        </span>
      )}
    </div>
    <h3 className="text-2xl font-bold text-foreground mb-1">{value}</h3>
    <p className="text-sm text-foreground-secondary font-medium">{title}</p>
    {subtext && <p className="text-xs text-foreground-tertiary mt-2">{subtext}</p>}
  </div>
);

const BuyerDashboard = () => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 800); // Reduced to 0.8 seconds
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div className="flex items-end justify-between pb-6 border-b border-border">
          <div>
            <h2 className="text-3xl font-bold text-foreground">My Collection</h2>
            <p className="text-foreground-secondary mt-1">Manage your NFT tickets and access passes.</p>
          </div>
          <Skeleton className="h-9 w-32 rounded" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <TicketSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-end justify-between pb-6 border-b border-border">
        <div>
          <h2 className="text-3xl font-bold text-foreground">My Collection</h2>
          <p className="text-foreground-secondary mt-1">Manage your NFT tickets and access passes.</p>
        </div>
        <Link to="/" className="btn-secondary text-sm flex items-center gap-2 hover:text-primary transition-colors">
          Browse Events <ArrowRight size={14} />
        </Link>
      </div>

      {MOCK_MY_TICKETS.length === 0 ? (
        <div className="py-20 text-center border border-dashed border-border rounded-xl bg-background-elevated/50">
          <Ticket className="mx-auto h-12 w-12 text-foreground-tertiary mb-4" />
          <h3 className="text-lg font-medium text-foreground">No tickets yet</h3>
          <p className="text-foreground-secondary mb-6">Start your collection today.</p>
          <Link to="/" className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-hover transition-colors">
            Explore Marketplace
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {MOCK_MY_TICKETS.map((ticket) => {
            const event = MOCK_EVENTS.find(e => e.id === ticket.eventId);
            return (
              <div key={ticket.id} className="group bg-background-elevated border border-border rounded-xl overflow-hidden card-hover">
                <div className="h-40 relative overflow-hidden bg-background-hover">
                  {event && <img src={event.imageUrl} className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-700" />}
                  <div className="absolute top-3 right-3">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs font-bold border backdrop-blur-sm",
                      ticket.status === 'VALID' ? "bg-success/20 border-success/30 text-success" : "bg-warning/20 border-warning/30 text-warning"
                    )}>
                      {ticket.status}
                    </span>
                  </div>
                </div>
                <div className="p-5">
                  <h3 className="font-bold text-lg text-foreground mb-1">{event?.title}</h3>
                  <p className="text-xs font-mono text-primary mb-4">#{ticket.tokenId}</p>

                  <div className="flex gap-3">
                    <button className="flex-1 bg-foreground text-background py-2 rounded text-sm font-medium hover:opacity-90 transition-opacity">
                      View QR
                    </button>
                    <button className="flex-1 border border-border text-foreground-secondary py-2 rounded text-sm font-medium hover:text-foreground hover:border-foreground transition-colors">
                      Sell
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const OrganizerDashboard = () => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 800); // Reduced to 0.8 seconds
    return () => clearTimeout(timer);
  }, []);

  const salesData = [
    { name: 'Mon', sales: 40 }, { name: 'Tue', sales: 30 },
    { name: 'Wed', sales: 60 }, { name: 'Thu', sales: 45 },
    { name: 'Fri', sales: 80 }, { name: 'Sat', sales: 55 },
    { name: 'Sun', sales: 70 },
  ];

  if (isLoading) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div className="flex items-center justify-between pb-6 border-b border-border">
          <div>
            <h2 className="text-3xl font-bold text-foreground">Organizer Studio</h2>
            <p className="text-foreground-secondary mt-1">Analytics and event management.</p>
          </div>
          <Skeleton className="h-10 w-36 rounded" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 bg-background-elevated p-6 rounded-xl border border-border">
            <Skeleton className="h-6 w-32 mb-6" />
            <div className="h-64 flex items-center justify-center">
              <React.Suspense fallback={<Skeleton className="w-[300px] h-[300px] rounded-full" />}>
                <NFTCoinAnimation />
              </React.Suspense>
            </div>
          </div>

          <div className="bg-background-elevated p-6 rounded-xl border border-border">
            <Skeleton className="h-6 w-32 mb-6" />
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg">
                  <Skeleton className="w-10 h-10 rounded" />
                  <div className="flex-1">
                    <Skeleton className="h-4 w-32 mb-2" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between pb-6 border-b border-border">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Organizer Studio</h2>
          <p className="text-foreground-secondary mt-1">Analytics and event management.</p>
        </div>
        <Link to="/create-event" className="flex items-center gap-2 bg-primary hover:bg-primary-hover text-white px-4 py-2 rounded font-medium transition-all">
          <Plus size={16} /> Create Event
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Total Revenue" value="45.2 ETH" icon={DollarSign} trend="+12.5%" subtext="Lifetime earnings" />
        <StatCard title="Tickets Sold" value="1,240" icon={Ticket} trend="+5.2%" subtext="Across 3 events" />
        <StatCard title="Active Events" value="3" icon={Calendar} subtext="Next: tomorrow" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Chart */}
        <div className="lg:col-span-2 bg-background-elevated p-6 rounded-xl border border-border">
          <h3 className="text-lg font-bold mb-6 text-foreground">Sales Volume</h3>
          <div className="h-64">
            <React.Suspense fallback={<Skeleton className="w-full h-full" />}>
              <LazyChart data={salesData} />
            </React.Suspense>
          </div>
        </div>

        {/* Recent List */}
        <div className="bg-background-elevated p-6 rounded-xl border border-border">
          <h3 className="text-lg font-bold mb-6 text-foreground">Active Events</h3>
          <div className="space-y-4">
            {MOCK_EVENTS.slice(0, 3).map(evt => (
              <div key={evt.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-background-hover transition-colors cursor-pointer group">
                <div className="w-10 h-10 rounded bg-background-hover overflow-hidden">
                  <img src={evt.imageUrl} className="w-full h-full object-cover" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{evt.title}</p>
                  <p className="text-xs text-foreground-tertiary">{evt.soldTickets}/{evt.totalTickets} sold</p>
                </div>
                <ArrowRight size={14} className="text-foreground-tertiary group-hover:text-primary" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const AdminView = () => (
  <div className="text-center py-20 bg-background-elevated border border-border rounded-xl">
    <Shield size={48} className="mx-auto text-error mb-4" />
    <h2 className="text-2xl font-bold text-foreground">Admin Portal</h2>
    <p className="text-foreground-secondary mb-6">System configuration and user management.</p>
    <Link to="/admin" className="text-primary hover:underline underline-offset-4">Access Admin Dashboard &rarr;</Link>
  </div>
);

export const Dashboard: React.FC = () => {
  const { isConnected, userRole } = useWeb3();

  if (!isConnected) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-4">
        <div className="bg-background-elevated p-8 rounded-2xl border border-border max-w-md w-full shadow-2xl min-h-[300px] flex flex-col justify-center">
          <Shield className="w-12 h-12 text-foreground-tertiary mx-auto mb-4" />
          <h2 className="text-xl font-bold text-foreground mb-2">Wallet Connection Required</h2>
          <p className="text-foreground-secondary mb-6">Please connect your wallet to access the dashboard.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-slide-up">
      {userRole === UserRole.BUYER && <BuyerDashboard />}
      {userRole === UserRole.ORGANIZER && <OrganizerDashboard />}
      {userRole === UserRole.RESELLER && <BuyerDashboard />} {/* Reusing Buyer UI for Reseller MVP */}
      {userRole === UserRole.ADMIN && <AdminView />}
      {userRole === UserRole.SCANNER && (
        <div className="text-center py-20">
          <h2 className="text-2xl font-bold text-foreground mb-4">Scanner Account</h2>
          <Link to="/scanner" className="px-6 py-3 bg-success text-background font-bold rounded-lg hover:bg-success-light">
            Launch Scanner Tool
          </Link>
        </div>
      )}
    </div>
  );
};

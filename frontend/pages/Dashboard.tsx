// File header: Dashboard page displaying user-specific content based on role.
// Shows buyer collection, organizer analytics, or admin portal based on user role.

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useWeb3 } from '../services/web3Context';
import { useAuth } from '../services/authContext';
import { UserRole, type Event, type Ticket } from '../types';
import { Ticket as TicketIcon, Plus, TrendingUp, Shield, DollarSign, Calendar, ArrowRight } from 'lucide-react';
import { getEvents, getOrganizerStats, type EventResponse, type OrganizerStats } from '../services/eventService';
import { getUserTickets } from '../services/ticketService';
import { Skeleton } from '../components/ui/skeleton';
import { cn, formatCurrency } from '../lib/utils';
import { SellTicketModal } from '../components/SellTicketModal';

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
  const { t } = useTranslation();
  const { address } = useWeb3();
  const [isLoading, setIsLoading] = useState(true);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicketForSale, setSelectedTicketForSale] = useState<Ticket | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!address) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        // Fetch user tickets and events in parallel
        const [userTickets, allEvents] = await Promise.all([
          getUserTickets(address),
          getEvents(),
        ]);

        // Map API events to frontend Event interface
        const mappedEvents: Event[] = allEvents.map((e: EventResponse) => ({
          id: e.id.toString(),
          title: e.name,
          description: e.description,
          date: e.date,
          location: e.location,
          imageUrl: e.image_url || 'https://picsum.photos/800/400?random=' + e.id,
          price: e.price,
          currency: (e.currency as 'ETH' | 'MATIC') || 'ETH',
          totalTickets: e.total_tickets,
          soldTickets: e.sold_tickets || 0,
          organizer: e.organizer_address || 'unknown',
          category: e.category || 'All',
        }));

        setTickets(userTickets);
        setEvents(mappedEvents);
      } catch (err: any) {
        console.error('Failed to fetch data:', err);
        setError(err.message || 'Failed to load data');
        setTickets([]);
        setEvents([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [address]);

  if (isLoading) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div className="flex items-end justify-between pb-6 border-b border-border">
          <div>
            <h2 className="text-3xl font-bold text-foreground">{t('dashboard.myCollection')}</h2>
            <p className="text-foreground-secondary mt-1">{t('dashboard.myCollectionDesc')}</p>
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
    <>
      <div className="space-y-8 animate-fade-in">
        <div className="flex items-end justify-between pb-6 border-b border-border">
          <div>
            <h2 className="text-3xl font-bold text-foreground">{t('dashboard.myCollection')}</h2>
            <p className="text-foreground-secondary mt-1">{t('dashboard.myCollectionDesc')}</p>
          </div>
          <Link to="/" className="btn-secondary text-sm flex items-center gap-2 hover:text-primary transition-colors">
            {t('dashboard.browseEvents')} <ArrowRight size={14} />
          </Link>
        </div>

      {error ? (
        <div className="py-20 text-center border border-dashed border-border rounded-xl bg-background-elevated/50">
          <p className="text-foreground-secondary">{error}</p>
        </div>
      ) : tickets.length === 0 ? (
        <div className="py-20 text-center border border-dashed border-border rounded-xl bg-background-elevated/50">
          <TicketIcon className="mx-auto h-12 w-12 text-foreground-tertiary mb-4" />
          <h3 className="text-lg font-medium text-foreground">{t('dashboard.noTickets')}</h3>
          <p className="text-foreground-secondary mb-6">{t('dashboard.noTicketsDesc')}</p>
          <Link to="/" className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-hover transition-colors">
            {t('dashboard.exploreMarketplace')}
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tickets.map((ticket) => {
            const event = events.find(e => e.id === ticket.eventId);
            return (
              <div key={ticket.id} className="group bg-background-elevated border border-border rounded-xl overflow-hidden card-hover">
                <div className="h-40 relative overflow-hidden bg-background-hover">
                  {event && <img src={event.imageUrl} className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-700" alt={event.title} />}
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
                  <h3 className="font-bold text-lg text-foreground mb-1">{event?.title || 'Unknown Event'}</h3>
                  <p className="text-xs font-mono text-primary mb-4">#{ticket.tokenId}</p>

                  <div className="flex gap-3">
                    <button className="flex-1 bg-foreground text-background py-2 rounded text-sm font-medium hover:opacity-90 transition-opacity">
                      {t('dashboard.viewQR')}
                    </button>
                    <button
                      onClick={() => setSelectedTicketForSale(ticket)}
                      className="flex-1 border border-border text-foreground-secondary py-2 rounded text-sm font-medium hover:text-foreground hover:border-foreground transition-colors"
                    >
                      {t('dashboard.sell')}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
      </div>
      {selectedTicketForSale && (
        <SellTicketModal
          ticketId={selectedTicketForSale.id}
          eventId={selectedTicketForSale.eventId}
          originalPrice={selectedTicketForSale.purchasePrice || 0}
          isOpen={!!selectedTicketForSale}
          onClose={() => setSelectedTicketForSale(null)}
          onListSuccess={() => {
            setSelectedTicketForSale(null);
            // Refresh tickets
            if (address) {
              getUserTickets(address).then(setTickets).catch(console.error);
            }
          }}
        />
      )}
    </>
  );
};

const OrganizerDashboard = () => {
  const { t } = useTranslation();
  const { address } = useWeb3();
  const [isLoading, setIsLoading] = useState(true);
  const [events, setEvents] = useState<Event[]>([]);
  const [stats, setStats] = useState<OrganizerStats | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!address) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        // Fetch events and stats in parallel
        const [apiEvents, organizerStats] = await Promise.all([
          getEvents(),
          getOrganizerStats(address),
        ]);

        // Map API response to frontend Event interface
        const mappedEvents: Event[] = apiEvents.map((e: EventResponse) => ({
          id: e.id.toString(),
          title: e.name,
          description: e.description,
          date: e.date,
          location: e.location,
          imageUrl: e.image_url || 'https://picsum.photos/800/400?random=' + e.id,
          price: e.price,
          currency: (e.currency as 'ETH' | 'MATIC') || 'ETH',
          totalTickets: e.total_tickets,
          soldTickets: e.sold_tickets || 0,
          organizer: e.organizer_address || 'unknown',
          category: e.category || 'All',
        }));
        
        // Filter to show only organizer's events
        const organizerEvents = mappedEvents.filter(e => e.organizer.toLowerCase() === address.toLowerCase());
        setEvents(organizerEvents);
        setStats(organizerStats);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setEvents([]);
        setStats(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [address]);

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
            <h2 className="text-3xl font-bold text-foreground">{t('dashboard.organizerStudio')}</h2>
            <p className="text-foreground-secondary mt-1">{t('dashboard.organizerStudioDesc')}</p>
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
          <h2 className="text-3xl font-bold text-foreground">{t('dashboard.organizerStudio')}</h2>
          <p className="text-foreground-secondary mt-1">{t('dashboard.organizerStudioDesc')}</p>
        </div>
        <Link to="/create-event" className="flex items-center gap-2 bg-primary hover:bg-primary-hover text-white px-4 py-2 rounded font-medium transition-all">
          <Plus size={16} /> {t('dashboard.createEvent')}
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title={t('dashboard.totalRevenue')} 
          value={stats ? `${stats.total_revenue.toFixed(2)} ETH` : '0.00 ETH'} 
          icon={DollarSign} 
          trend={stats && stats.total_revenue > 0 ? "+12.5%" : undefined} 
          subtext={t('dashboard.lifetimeEarnings')} 
        />
        <StatCard 
          title={t('dashboard.ticketsSold')} 
          value={stats ? stats.tickets_sold.toLocaleString() : '0'} 
          icon={TicketIcon} 
          trend={stats && stats.tickets_sold > 0 ? "+5.2%" : undefined} 
          subtext={t('dashboard.acrossEvents')} 
        />
        <StatCard 
          title={t('dashboard.activeEvents')} 
          value={stats ? stats.active_events.toString() : '0'} 
          icon={Calendar} 
          subtext={t('dashboard.nextTomorrow')} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Chart */}
        <div className="lg:col-span-2 bg-background-elevated p-6 rounded-xl border border-border">
          <h3 className="text-lg font-bold mb-6 text-foreground">{t('dashboard.salesVolume')}</h3>
          <div className="h-64">
            <React.Suspense fallback={<Skeleton className="w-full h-full" />}>
              <LazyChart data={salesData} />
            </React.Suspense>
          </div>
        </div>

        {/* Recent List */}
        <div className="bg-background-elevated p-6 rounded-xl border border-border">
          <h3 className="text-lg font-bold mb-6 text-foreground">{t('dashboard.activeEventsList')}</h3>
          <div className="space-y-4">
            {isLoading ? (
              [...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg">
                  <Skeleton className="w-10 h-10 rounded" />
                  <div className="flex-1">
                    <Skeleton className="h-4 w-32 mb-2" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                </div>
              ))
            ) : events.length === 0 ? (
              <div className="text-center py-4 text-foreground-secondary text-sm">
                {t('dashboard.noEvents') || 'No events yet'}
              </div>
            ) : (
              events.slice(0, 3).map(evt => (
                <Link
                  key={evt.id}
                  to={`/event/${evt.id}`}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-background-hover transition-colors cursor-pointer group"
                >
                  <div className="w-10 h-10 rounded bg-background-hover overflow-hidden">
                    <img src={evt.imageUrl} className="w-full h-full object-cover" alt={evt.title} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{evt.title}</p>
                    <p className="text-xs text-foreground-tertiary">{evt.soldTickets}/{evt.totalTickets} {t('dashboard.sold')}</p>
                  </div>
                  <ArrowRight size={14} className="text-foreground-tertiary group-hover:text-primary" />
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const AdminView = () => {
  const { t } = useTranslation();
  return (
    <div className="text-center py-20 bg-background-elevated border border-border rounded-xl">
      <Shield size={48} className="mx-auto text-error mb-4" />
      <h2 className="text-2xl font-bold text-foreground">{t('dashboard.adminPortal')}</h2>
      <p className="text-foreground-secondary mb-6">{t('dashboard.adminPortalDesc')}</p>
      <Link to="/admin" className="text-primary hover:underline underline-offset-4">{t('dashboard.accessAdminDashboard')}</Link>
    </div>
  );
};

export const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const { isConnected } = useWeb3();
  const { user } = useAuth();

  // Get user's actual role from authentication context
  const userRole = user?.role ? (user.role.toUpperCase() as UserRole) : UserRole.BUYER;

  if (!isConnected) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-4">
        <div className="bg-background-elevated p-8 rounded-2xl border border-border max-w-md w-full shadow-2xl min-h-[300px] flex flex-col justify-center">
          <Shield className="w-12 h-12 text-foreground-tertiary mx-auto mb-4" />
          <h2 className="text-xl font-bold text-foreground mb-2">{t('dashboard.walletConnectionRequired')}</h2>
          <p className="text-foreground-secondary mb-6">{t('dashboard.walletConnectionDesc')}</p>
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
          <h2 className="text-2xl font-bold text-foreground mb-4">{t('dashboard.scannerAccount')}</h2>
          <Link to="/scanner" className="px-6 py-3 bg-success text-background font-bold rounded-lg hover:bg-success-light">
            {t('dashboard.launchScannerTool')}
          </Link>
        </div>
      )}
    </div>
  );
};

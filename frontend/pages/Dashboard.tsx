// File header: Dashboard page displaying user-specific content based on role.
// Shows buyer collection, organizer analytics, or admin portal based on user role.

import React, { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useWeb3 } from '../services/web3Context';
import { useAuth } from '../services/authContext';
import { UserRole, type Event, type Ticket } from '../types';
import { Ticket as TicketIcon, Plus, TrendingUp, Shield, DollarSign, Calendar, ArrowRight, AlertCircle } from 'lucide-react';
import { getOrganizerStats, getEvent, type OrganizerStats } from '../services/eventService';
import { useEvents, useUserTickets } from '../services/swrConfig';
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

const BuyerDashboard = React.memo(() => {
  const { t } = useTranslation();
  const { address } = useWeb3();
  const [selectedTicketForSale, setSelectedTicketForSale] = useState<Ticket | null>(null);
  
  // Use SWR for automatic caching
  const { data: userTickets, error: ticketsError, isLoading: isLoadingTickets, mutate: mutateTickets } = useUserTickets(address);
  const { data: apiEvents, error: eventsError, isLoading: isLoadingEvents } = useEvents();
  
  const isLoading = isLoadingTickets || isLoadingEvents;
  
  // CRITICAL: Distinguish between actual errors and empty states
  // Empty tickets array is NOT an error - it's a normal state
  const hasActualError = ticketsError && ticketsError.message && !ticketsError.message.includes('404');
  const error = hasActualError ? ticketsError?.message : (eventsError?.message || null);
  
  // Memoize mapped events - ensure IDs match ticket event_id values
  const events = useMemo<Event[]>(() => {
    if (!apiEvents) return [];
    
    console.log('Mapping events from API:', apiEvents);
    
    return apiEvents.map((e) => {
      // The API returns 'id' which should be event_id from database
      // Handle both 'id' and 'event_id' fields for compatibility
      let eventId = (e as any).event_id;
      if (eventId === undefined || eventId === null) {
        eventId = e.id;
      }
      
      // Ensure eventId is a number, then convert to string for consistency
      const eventIdNum = Number(eventId);
      const eventIdStr = !isNaN(eventIdNum) ? eventIdNum.toString() : String(eventId || '');
      
      console.log(`Mapping event: name="${e.name}", id=${e.id}, event_id=${(e as any).event_id}, finalId=${eventIdStr}`);
      
      return {
        id: eventIdStr,
        title: e.name,
        description: e.description,
        date: e.date,
        location: e.location,
        imageUrl: e.image_url || 'https://picsum.photos/800/400?random=' + eventIdNum,
        price: e.price,
        currency: (e.currency as 'ETH' | 'MATIC') || 'ETH',
        totalTickets: e.total_tickets,
        soldTickets: e.sold_tickets || 0,
        organizer: e.organizer_address || 'unknown',
        category: e.category || 'All',
      };
    });
  }, [apiEvents]);
  
  // Show all tickets, even if they don't have matching events
  // This allows users to see their tickets even if events were deleted
  const tickets = React.useMemo(() => {
    const allTickets = userTickets || [];
    
    // Filter out only completely invalid tickets (no ID)
    const validTickets = allTickets.filter(ticket => 
      ticket && ticket.id
    );
    
    // Debug: Log eventName for each ticket - EXPAND FULL OBJECT
    console.log('🔍 Tickets with eventName (FULL):', validTickets.map(t => ({
      id: t.id,
      eventId: t.eventId,
      eventIdType: typeof t.eventId,
      eventName: t.eventName,
      eventNameType: typeof t.eventName,
      hasEventName: !!t.eventName,
      fullTicket: t  // Show full ticket object
    })));
    
    return validTickets;
  }, [userTickets]);
  
  // Fetch missing events individually if they're not in the list
  const [missingEvents, setMissingEvents] = React.useState<Map<string, Event>>(new Map());
  
  React.useEffect(() => {
    if (!tickets || tickets.length === 0) return;
    
    // Find ticket eventIds that don't have matching events
    const ticketEventIds = tickets
      .map(t => t.eventId)
      .filter(eventId => eventId && eventId !== '0' && eventId !== 0 && eventId !== undefined && eventId !== null)
      .filter((eventId, index, self) => self.indexOf(eventId) === index); // Remove duplicates
    
    // Check which eventIds are missing from the events list
    const missingEventIds = ticketEventIds.filter(eventId => {
      const eventIdNum = Number(eventId);
      if (isNaN(eventIdNum)) return false;
      
      // Check if event exists in the main events list
      const existsInEvents = events.some(e => {
        const eIdNum = Number(e.id);
        return !isNaN(eIdNum) && eIdNum === eventIdNum;
      });
      
      // Check if we've already fetched it
      const existsInMissing = missingEvents.has(eventId.toString());
      
      return !existsInEvents && !existsInMissing;
    });
    
    // Fetch missing events - use Promise.all for parallel fetching
    if (missingEventIds.length > 0) {
      console.log('🔍 Fetching missing events for tickets:', missingEventIds);
      console.log('   Current events in list:', events.map(e => e.id));
      console.log('   Ticket eventIds needed:', ticketEventIds);
      
      // Fetch all missing events in parallel
      Promise.all(
        missingEventIds.map(async (eventId) => {
          try {
            const eventIdNum = Number(eventId);
            if (isNaN(eventIdNum)) {
              console.warn(`⚠️ Invalid eventId: ${eventId}`);
              return null;
            }
            
            console.log(`   Fetching event ${eventIdNum}...`);
            const eventResponse = await getEvent(eventIdNum);
            const mappedEvent: Event = {
              id: eventResponse.id.toString(),
              title: eventResponse.name,
              description: eventResponse.description,
              date: eventResponse.date,
              location: eventResponse.location,
              imageUrl: eventResponse.image_url || 'https://picsum.photos/800/400?random=' + eventResponse.id,
              price: eventResponse.price,
              currency: (eventResponse.currency as 'ETH' | 'MATIC') || 'ETH',
              totalTickets: eventResponse.total_tickets,
              soldTickets: eventResponse.sold_tickets || 0,
              organizer: eventResponse.organizer_address || 'unknown',
              category: eventResponse.category || 'All',
            };
            
            console.log(`✅ Fetched missing event: "${mappedEvent.title}" (id: ${mappedEvent.id})`);
            return { eventId: eventId.toString(), event: mappedEvent };
          } catch (err) {
            console.warn(`❌ Failed to fetch event ${eventId}:`, err);
            // If event doesn't exist, we'll show "Unknown Event" - this is expected for deleted events
            return null;
          }
        })
      ).then(results => {
        // Update state with all fetched events at once
        setMissingEvents(prev => {
          const newMap = new Map(prev);
          results.forEach(result => {
            if (result && result.event) {
              newMap.set(result.eventId, result.event);
            }
          });
          return newMap;
        });
      });
    } else if (ticketEventIds.length > 0) {
      console.log('✅ All ticket eventIds have matching events:', ticketEventIds);
    }
  }, [tickets, events, missingEvents]);
  
  // Merge missing events into events array
  const allEvents = React.useMemo(() => {
    const eventsMap = new Map<string, Event>();
    events.forEach(e => eventsMap.set(e.id, e));
    missingEvents.forEach((e, id) => {
      eventsMap.set(id, e);
      console.log(`📌 Added missing event to allEvents: "${e.title}" (id: ${e.id})`);
    });
    const all = Array.from(eventsMap.values());
    console.log(`📊 Total events in allEvents: ${all.length} (${events.length} from API + ${missingEvents.size} fetched)`);
    return all;
  }, [events, missingEvents]);
  
  // Debug: Log tickets and events for troubleshooting
  React.useEffect(() => {
    console.log('=== COMPREHENSIVE TICKET/EVENT DEBUG ===');
    console.log('1. Raw API Events:', JSON.stringify(apiEvents, null, 2));
    console.log('2. Mapped Events:', events.map(e => ({ id: e.id, idType: typeof e.id, title: e.title, idAsNumber: Number(e.id) })));
    console.log('3. Raw User Tickets:', JSON.stringify(userTickets, null, 2));
    console.log('4. Processed Tickets:', tickets.map(t => ({ id: t.id, eventId: t.eventId, eventIdType: typeof t.eventId, eventName: t.eventName })));
    console.log('5. All Events (with missing):', allEvents.map(e => ({ id: e.id, title: e.title })));
    
    if (tickets.length > 0) {
      console.log('\n=== TICKET EVENT MATCHING ANALYSIS ===');
      tickets.forEach(ticket => {
        const ticketEventId = ticket.eventId;
        const ticketEventIdNum = Number(ticketEventId);
        
        console.log(`\n📋 Ticket ${ticket.id}:`);
        console.log(`   - eventId: "${ticketEventId}" (type: ${typeof ticketEventId}, as number: ${ticketEventIdNum})`);
        
        // Check in regular events
        const matchedInEvents = events.find(e => {
          if (!e || !e.id) return false;
          const eventIdNum = Number(e.id);
          return !isNaN(eventIdNum) && !isNaN(ticketEventIdNum) && eventIdNum === ticketEventIdNum;
        });
        
        // Check in allEvents (includes missing events)
        const matchedInAll = allEvents.find(e => {
          if (!e || !e.id) return false;
          const eventIdNum = Number(e.id);
          return !isNaN(eventIdNum) && !isNaN(ticketEventIdNum) && eventIdNum === ticketEventIdNum;
        });
        
        if (matchedInAll) {
          console.log(`   ✅ MATCHED: "${matchedInAll.title}" (id: ${matchedInAll.id})`);
        } else {
          console.log(`   ❌ NO MATCH FOUND`);
          console.log(`   Available event IDs:`, allEvents.map(e => `${e.id} (${typeof e.id})`).join(', '));
          console.log(`   Looking for: ${ticketEventIdNum} (from "${ticketEventId}")`);
        }
      });
    }
  }, [tickets, events, userTickets, apiEvents, allEvents]);
  
  // Memoize refresh callback
  const handleListSuccess = useCallback(() => {
    setSelectedTicketForSale(null);
    if (address) {
      mutateTickets(); // Refresh tickets cache
    }
  }, [address, mutateTickets]);

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
          <AlertCircle className="mx-auto h-12 w-12 text-error mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">{t('dashboard.errorLoadingTickets', 'Error Loading Tickets')}</h3>
          <p className="text-foreground-secondary mb-6">{error}</p>
          <button
            onClick={() => mutateTickets()}
            className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-hover transition-colors"
          >
            {t('common.retry', 'Retry')}
          </button>
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
          {tickets
            .filter(ticket => ticket && ticket.id) // Filter out invalid tickets
            .map((ticket) => {
            // Match event by ID - tickets have event_id (6, 4) from database
            // Events API returns id field which is event_id from database
            let matchedEvent: Event | undefined = undefined;
            
            if (ticket.eventId && ticket.eventId !== '0' && ticket.eventId !== 0) {
              // Convert ticket eventId to number for comparison
              const ticketEventIdNum = Number(ticket.eventId);
              const ticketEventIdStr = String(ticket.eventId).trim();
              
              if (!isNaN(ticketEventIdNum) && allEvents.length > 0) {
                // Find event by numeric ID match - use allEvents which includes missing events
                matchedEvent = allEvents.find(e => {
                  if (!e || !e.id) return false;
                  
                  // Strategy 1: Direct numeric comparison (most reliable)
                  const eventIdNum = Number(e.id);
                  if (!isNaN(eventIdNum) && !isNaN(ticketEventIdNum) && eventIdNum === ticketEventIdNum) {
                    return true;
                  }
                  
                  // Strategy 2: String comparison (fallback)
                  const eventIdStr = String(e.id).trim();
                  if (eventIdStr === ticketEventIdStr) {
                    return true;
                  }
                  
                  return false;
                });
              }
              
              // Debug: Log matching attempt (only in dev)
              if ((import.meta as any).env?.DEV) {
                if (!matchedEvent) {
                  console.warn(`⚠️ No event found for ticket ${ticket.id} with eventId ${ticket.eventId}`);
                  console.log(`   Ticket eventId: ${ticket.eventId} (type: ${typeof ticket.eventId}, as number: ${ticketEventIdNum})`);
                  console.log(`   Total events available: ${allEvents.length}`);
                  console.log('   Available event IDs:', allEvents.map(e => ({ 
                    id: e.id, 
                    idType: typeof e.id,
                    idAsNumber: Number(e.id),
                    title: e.title 
                  })));
                } else {
                  console.log(`✅ Ticket ${ticket.id} matched to: "${matchedEvent.title}" (event ID: ${matchedEvent.id})`);
                }
              }
            }
            
            // Show tickets even without eventId (event might have been deleted)
            
            return (
              <div key={ticket.id} className="group bg-background-elevated border border-border rounded-xl overflow-hidden card-hover">
                <div className="h-40 relative overflow-hidden bg-background-hover">
                  {matchedEvent && <img loading="lazy" src={matchedEvent.imageUrl} className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-700" alt={matchedEvent.title} />}
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
                  <h3 className="font-bold text-lg text-foreground mb-1">
                    {ticket.eventName || matchedEvent?.title || (ticket.eventId && ticket.eventId !== '0' && ticket.eventId !== 0 ? `Event #${ticket.eventId}` : 'Unknown Event')}
                  </h3>
                  <p className="text-xs font-mono text-primary mb-4">
                    #{ticket.tokenId || ticket.id || 'N/A'}
                  </p>

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
          })
          .filter(Boolean) // Remove null entries
          }
        </div>
      )}
      </div>
      {selectedTicketForSale && (
        <SellTicketModal
          ticketId={parseInt(selectedTicketForSale.id, 10)}
          eventId={selectedTicketForSale.eventId ? parseInt(selectedTicketForSale.eventId.toString(), 10) : 0}
          originalPrice={selectedTicketForSale.pricePaid || 0}
          isOpen={!!selectedTicketForSale}
          onClose={() => setSelectedTicketForSale(null)}
          onListSuccess={handleListSuccess}
        />
      )}
    </>
  );
});

const OrganizerDashboard = React.memo(() => {
  const { t } = useTranslation();
  const { address } = useWeb3();
  const [stats, setStats] = useState<OrganizerStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  
  // Use SWR for events
  const { data: apiEvents, error: eventsError, isLoading: isLoadingEvents } = useEvents();
  
  const isLoading = isLoadingEvents || isLoadingStats;
  
  // Memoize mapped and filtered events
  const events = useMemo<Event[]>(() => {
    if (!apiEvents || !address) return [];
    
    const mappedEvents: Event[] = apiEvents.map((e) => ({
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
    return mappedEvents.filter(e => e.organizer.toLowerCase() === address.toLowerCase());
  }, [apiEvents, address]);
  
  // Fetch stats separately (not cached with SWR since it's user-specific)
  React.useEffect(() => {
    if (!address) {
      setIsLoadingStats(false);
      return;
    }
    
    setIsLoadingStats(true);
    getOrganizerStats(address)
      .then(setStats)
      .catch(err => {
        console.error('Failed to fetch stats:', err);
        setStats(null);
      })
      .finally(() => setIsLoadingStats(false));
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
                    <img loading="lazy" src={evt.imageUrl} className="w-full h-full object-cover" alt={evt.title} />
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
});

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
      <div className="flex-grow flex flex-col items-center justify-center text-center p-4">
        <div className="bg-background-elevated p-8 rounded-2xl border border-border max-w-md w-full shadow-2xl min-h-[300px] flex flex-col justify-center">
          <Shield className="w-12 h-12 text-foreground-tertiary mx-auto mb-4" />
          <h2 className="text-xl font-bold text-foreground mb-2">{t('dashboard.walletConnectionRequired')}</h2>
          <p className="text-foreground-secondary mb-6">{t('dashboard.walletConnectionDesc')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-slide-up flex flex-col flex-grow" style={{ flexGrow: 1, minHeight: 0 }}>
      {userRole === UserRole.BUYER && <BuyerDashboard />}
      {userRole === UserRole.ORGANIZER && <OrganizerDashboard />}
      {userRole === UserRole.RESELLER && <BuyerDashboard />} {/* Reusing Buyer UI for Reseller MVP */}
      {userRole === UserRole.ADMIN && <AdminView />}
      {userRole === UserRole.SCANNER && (
        <div className="text-center py-20 flex-grow flex flex-col items-center justify-center">
          <h2 className="text-2xl font-bold text-foreground mb-4">{t('dashboard.scannerAccount')}</h2>
          <Link to="/scanner" className="px-6 py-3 bg-success text-background font-bold rounded-lg hover:bg-success-light">
            {t('dashboard.launchScannerTool')}
          </Link>
        </div>
      )}
    </div>
  );
};

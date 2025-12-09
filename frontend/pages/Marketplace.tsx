// File header: Marketplace page displaying available NFT ticket events.
// Supports filtering, searching, and browsing events by category.

import React, { useState, useMemo, Suspense, useDeferredValue } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, MapPin, Search, ArrowRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useEvents, useResaleListings } from '../services/swrConfig';
import { getTicket } from '../services/ticketService';
import { Event } from '../types';
import { NFTCoinAnimation } from '../components/3d/NFTCoinAnimation';
import { TicketCardSkeleton } from '../components/ui/TicketCardSkeleton';
import { ResaleListingCard } from '../components/ResaleListingCard';
import { cn } from '../lib/utils';
import { getPlaceholderImage, getWebPUrl } from '../lib/imageUtils';

// Defer 3D animation loading to improve LCP
const DeferredCoinAnimation: React.FC = () => {
  const [shouldLoad, setShouldLoad] = React.useState(false);

  React.useEffect(() => {
    // Load after a delay to not block LCP
    const timer = setTimeout(() => {
      setShouldLoad(true);
    }, 2000); // Load after 2 seconds

    return () => clearTimeout(timer);
  }, []);

  if (!shouldLoad) {
    return <div className="w-[300px] h-[300px] flex items-center justify-center" />;
  }

  return (
    <Suspense fallback={<div className="w-[300px] h-[300px]" />}>
      <NFTCoinAnimation />
    </Suspense>
  );
};

export const Marketplace: React.FC = React.memo(() => {
  const { t, i18n } = useTranslation();
  const [filter, setFilter] = useState('');
  const [category, setCategory] = useState('All');
  
  // Use SWR for automatic caching and revalidation
  // Defer initial fetch slightly to allow initial render
  const { data: apiEvents, error: eventsError, isLoading } = useEvents();
  const { data: resaleListings, error: resalesError, isLoading: isLoadingResales } = useResaleListings();
  
  // Show immediate loading state for faster FCP
  const showLoading = isLoading || isLoadingResales;
  
  // Ensure resaleListings is an array (handle undefined/null)
  const safeResaleListings = resaleListings || [];

  // Memoize mapped events to prevent unnecessary recalculations
  const events = useMemo<Event[]>(() => {
    if (!apiEvents) return [];
    return apiEvents.map((e) => ({
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
  }, [apiEvents]);

  // Memoize resale events - only show events that have actual resale listings
  const resaleEvents = useMemo<Event[]>(() => {
    if (!resaleListings || resaleListings.length === 0 || !apiEvents) return [];
    
    // Create event map - match listings to events via ticket.event_id
    const eventMap = new Map<number, Event>();
    const eventIdsFromListings = new Set<number>();
    
    // Try to get event_id from listing if backend provides it
    resaleListings.forEach(listing => {
      const eventId = (listing as any)._event_id; // Internal field from backend
      if (eventId) {
        eventIdsFromListings.add(Number(eventId));
      }
    });
    
    // Only show events that have resale listings - don't show all events as fallback
    if (eventIdsFromListings.size === 0) {
      return []; // No event IDs found, return empty array
    }
    
    // Filter events to only those with resale listings
    const eventsToShow = apiEvents.filter(e => {
      const eventIdNum = Number(e.id);
      return eventIdsFromListings.has(eventIdNum);
    });
    
    eventsToShow.forEach(e => {
      const eventIdNum = Number(e.id);
      if (!eventMap.has(eventIdNum)) {
        eventMap.set(eventIdNum, {
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
        });
      }
    });
    
    return Array.from(eventMap.values());
  }, [resaleListings, apiEvents]);

  const error = eventsError?.message || resalesError?.message || null;

  // Memoize filtered events to prevent recalculation on every render
  // Use useDeferredValue for filter to prevent blocking during typing
  const deferredFilter = useDeferredValue(filter);
  const filteredEvents = useMemo(() => {
    if (!events.length) return [];
    return events.filter(e => {
      const searchLower = deferredFilter.toLowerCase();
      const matchesSearch = e.title.toLowerCase().includes(searchLower) || 
                           e.description.toLowerCase().includes(searchLower) ||
                           e.category.toLowerCase().includes(searchLower);
      const matchesCategory = category === 'All' || e.category === category;
      return matchesSearch && matchesCategory;
    });
  }, [events, deferredFilter, category]);

  return (
    <div className="space-y-16 animate-fade-in">
      {/* Hero Section - Render immediately for faster FCP */}
      <div className="relative flex flex-col md:flex-row items-center justify-between gap-12 pt-8 pb-16 border-b border-border">
        <div className="space-y-6 max-w-2xl z-10">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-medium">
            {t('marketplace.newProtocol', 'New Protocol')}
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground" data-cy="marketplace-title">
            {t('marketplace.title', 'Discover NFT Events')}
          </h1>
          <p className="text-xl text-foreground-secondary leading-relaxed max-w-lg" data-cy="marketplace-subtitle">
            {t('marketplace.subtitle', 'Buy, sell, and trade event tickets as NFTs on the blockchain')}
          </p>

          <div className="relative max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
            <input
              type="text"
              placeholder={t('marketplace.searchPlaceholder', 'Search events...')}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full bg-background-elevated border border-border rounded-lg pl-12 pr-4 py-3 text-foreground placeholder:text-foreground-tertiary focus:border-primary transition-colors"
            />
          </div>
        </div>

        <div className="hidden md:flex items-center justify-center relative">
          <div className="absolute inset-0 bg-primary/20 blur-[100px] rounded-full pointer-events-none" />
          {/* Defer 3D animation to not block LCP */}
          <DeferredCoinAnimation />
        </div>
      </div>

      {/* Filters Section */}
      <div id="browse-events">
        <h2 className="text-2xl font-bold text-foreground mb-4">{t('marketplace.browseEvents', 'Browse Events')}</h2>
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
          {[
            { key: 'all', label: t('marketplace.categories.all', 'All') },
            { key: 'Music', label: t('marketplace.categories.music', 'Music') },
            { key: 'Art', label: t('marketplace.categories.art', 'Art') },
            { key: 'Technology', label: t('marketplace.categories.technology', 'Technology') },
            { key: 'Sports', label: t('marketplace.categories.sports', 'Sports') }
          ].map((cat) => (
            <button
              key={cat.key}
              onClick={() => setCategory(cat.key === 'all' ? 'All' : cat.key)}
              className={cn(
                "px-4 py-1.5 rounded-full text-sm font-medium border transition-all whitespace-nowrap",
                (category === 'All' && cat.key === 'all') || category === cat.key
                  ? "bg-foreground text-background border-foreground"
                  : "bg-transparent text-foreground-secondary border-border hover:border-foreground-secondary"
              )}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-error/10 border border-error/20 text-error p-4 rounded-lg">
          {error}
        </div>
      )}

      {/* Grid with Loading State - Show skeleton immediately for better LCP */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {isLoading ? (
          // Show skeleton cards immediately - don't wait for API
          <>
            {[...Array(6)].map((_, i) => (
              <TicketCardSkeleton key={i} />
            ))}
          </>
        ) : filteredEvents.length === 0 ? (
          <div className="col-span-full text-center py-12 text-foreground-secondary">
            <p className="text-lg mb-2">No events found</p>
            <p className="text-sm">Try adjusting your search or filters</p>
          </div>
        ) : (
          // Show actual events after loading
          filteredEvents.map((event, index) => (
            <Link
              to={`/event/${event.id}`}
              key={event.id}
              className="group bg-background-elevated rounded-xl border border-border overflow-hidden card-hover"
            >
              <div 
                className="event-image-container" 
                style={{ aspectRatio: '16/9', minHeight: '200px' }}
                data-lcp-candidate={index === 0 ? 'true' : undefined}
                data-aspect-ratio="16/9"
              >
                {/* Preload critical LCP image */}
                {index === 0 && (
                  <link rel="preload" as="image" href={event.imageUrl} fetchpriority="high" />
                )}
                <img
                  src={event.imageUrl}
                  alt={event.title}
                  width="640"
                  height="360"
                  loading={index < 3 ? "eager" : "lazy"}
                  decoding="async"
                  fetchpriority={index === 0 ? "high" : index < 3 ? "high" : "auto"}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  style={{ 
                    aspectRatio: '16/9',
                    objectFit: 'cover',
                    backgroundColor: 'var(--color-background-hover)',
                    minHeight: '200px'
                  }}
                  onError={(e) => {
                    // Fallback to a simple gradient placeholder if image fails
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const placeholder = document.createElement('div');
                    placeholder.className = 'w-full h-full bg-gradient-to-br from-primary/20 to-primary/5';
                    placeholder.style.aspectRatio = '16/9';
                    target.parentElement?.appendChild(placeholder);
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background-elevated to-transparent opacity-60" />
                <div className="absolute top-3 right-3 bg-background/80 backdrop-blur px-2 py-1 rounded border border-border text-xs font-mono text-foreground">
                  {event.price} ETH
                </div>
              </div>

              <div className="p-5 space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-primary uppercase tracking-wider">{event.category}</span>
                    <span className="text-xs text-foreground-tertiary">{event.totalTickets - event.soldTickets} {t('marketplace.ticketsLeft', 'left')}</span>
                  </div>
                  <h3 className="text-lg font-bold text-foreground group-hover:text-primary transition-colors">{event.title}</h3>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-foreground-secondary">
                    <Calendar size={14} />
                    <span>{new Date(event.date).toLocaleDateString(i18n.language === 'az' ? 'az-AZ' : 'en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-foreground-secondary">
                    <MapPin size={14} />
                    <span>{event.location}</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-border flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-orange-500 to-yellow-500" />
                    <span className="text-xs text-foreground-secondary">{t('marketplace.by', 'by')} {event.organizer.slice(0, 6)}...</span>
                  </div>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Reselling Section */}
      <div id="reselling" className="mt-16">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-foreground">{t('marketplace.reselling', 'Resale Market')}</h2>
            <p className="text-foreground-secondary mt-1">{t('marketplace.resellingDesc', 'Buy tickets from other users')}</p>
          </div>
        </div>

        {/* Resale Listings Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {isLoadingResales ? (
            <>
              {[...Array(3)].map((_, i) => (
                <TicketCardSkeleton key={i} />
              ))}
            </>
          ) : safeResaleListings.length === 0 ? (
            <div className="col-span-full text-center py-12 text-foreground-secondary border border-dashed border-border rounded-xl bg-background-elevated/50">
              <p className="text-lg mb-2">{t('marketplace.noResales', 'No resale listings available')}</p>
              <p className="text-sm">{t('marketplace.noResalesDesc', 'Check back later for tickets')}</p>
            </div>
          ) : (
            safeResaleListings.map((listing) => (
              <ResaleListingCard
                key={listing.id}
                listing={listing}
                events={resaleEvents}
                t={t}
                i18n={i18n}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
});

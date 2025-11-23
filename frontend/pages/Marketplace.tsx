import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, MapPin, Search } from 'lucide-react';
import { MOCK_EVENTS } from '../services/mockData';
import { NFTCoinAnimation } from '../components/3d/NFTCoinAnimation';
import { TicketCardSkeleton } from '../components/ui/TicketCardSkeleton';
import { cn } from '../lib/utils';

export const Marketplace: React.FC = () => {
  const [filter, setFilter] = useState('');
  const [category, setCategory] = useState('All');
  const [isLoading, setIsLoading] = useState(true);

  // Simulate loading delay - only on initial mount
  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 800); // Reduced to 0.8 seconds

    return () => clearTimeout(timer);
  }, []); // Empty dependency array - only runs once

  const filteredEvents = MOCK_EVENTS.filter(e =>
    (e.title.toLowerCase().includes(filter.toLowerCase()) || e.category.toLowerCase().includes(filter.toLowerCase())) &&
    (category === 'All' || e.category === category)
  );

  return (
    <div className="space-y-16 animate-fade-in">
      {/* Hero Section */}
      <div className="relative flex flex-col md:flex-row items-center justify-between gap-12 pt-8 pb-16 border-b border-border">
        <div className="space-y-6 max-w-2xl z-10">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-medium">
            New Protocol V2 Live
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground">
            Collect Moments,<br />
            <span className="text-gradient-primary">Not Just Tickets.</span>
          </h1>
          <p className="text-xl text-foreground-secondary leading-relaxed max-w-lg">
            The decentralized marketplace for verifying, trading, and collecting event access as NFTs.
          </p>

          <div className="relative max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
            <input
              type="text"
              placeholder="Search events..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full bg-background-elevated border border-border rounded-lg pl-12 pr-4 py-3 text-foreground placeholder:text-foreground-tertiary focus:border-primary transition-colors"
            />
          </div>
        </div>

        <div className="hidden md:flex items-center justify-center relative">
          <div className="absolute inset-0 bg-primary/20 blur-[100px] rounded-full pointer-events-none" />
          <NFTCoinAnimation />
        </div>
      </div>

      {/* Filters Section */}
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-4">Browse Events</h2>
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
          {['All', 'Music', 'Art', 'Technology', 'Sports'].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={cn(
                "px-4 py-1.5 rounded-full text-sm font-medium border transition-all whitespace-nowrap",
                category === cat
                  ? "bg-foreground text-background border-foreground"
                  : "bg-transparent text-foreground-secondary border-border hover:border-foreground-secondary"
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid with Loading State */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {isLoading ? (
          // Show only 3 skeleton cards while loading
          <>
            {[...Array(3)].map((_, i) => (
              <TicketCardSkeleton key={i} />
            ))}
          </>
        ) : (
          // Show actual events after loading
          filteredEvents.map((event) => (
            <Link
              to={`/event/${event.id}`}
              key={event.id}
              className="group bg-background-elevated rounded-xl border border-border overflow-hidden card-hover"
            >
              <div className="event-image-container">
                <img
                  src={event.imageUrl}
                  alt={event.title}
                  width="640"
                  height="360"
                  loading="lazy"
                  decoding="async"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
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
                    <span className="text-xs text-foreground-tertiary">{event.totalTickets - event.soldTickets} left</span>
                  </div>
                  <h3 className="text-lg font-bold text-foreground group-hover:text-primary transition-colors">{event.title}</h3>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-foreground-secondary">
                    <Calendar size={14} />
                    <span>{new Date(event.date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-foreground-secondary">
                    <MapPin size={14} />
                    <span>{event.location}</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-border flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-orange-500 to-yellow-500" />
                    <span className="text-xs text-foreground-secondary">By {event.organizer.slice(0, 6)}...</span>
                  </div>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
};

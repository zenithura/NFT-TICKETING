// File header: Card component for displaying resale listings in the marketplace
// Shows ticket resale information with event details

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, MapPin, ArrowRight } from 'lucide-react';
import { getTicket } from '../services/ticketService';
import { Event } from '../types';
import { ResaleListing } from '../services/marketplaceService';
import { cn } from '../lib/utils';

interface ResaleListingCardProps {
  listing: ResaleListing;
  events: Event[];
  t: (key: string) => string;
  i18n: { language: string };
}

export const ResaleListingCard: React.FC<ResaleListingCardProps> = ({
  listing,
  events,
  t,
  i18n,
}) => {
  const [event, setEvent] = useState<Event | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        // Priority 1: Use event_name from listing (if available from backend)
        if (listing.event_name) {
          // Try to find event in the events list by name
          const foundEvent = events.find(e => e.title === listing.event_name);
          if (foundEvent) {
            setEvent(foundEvent);
            setIsLoading(false);
            return;
          }
          // If not found in events list, we'll still use the name for display
          // Create a minimal event object for display
          setEvent({
            id: '',
            title: listing.event_name,
            description: '',
            date: '',
            location: '',
            imageUrl: '',
            price: 0,
            currency: 'ETH',
            totalTickets: 0,
            soldTickets: 0,
            organizer: '',
            category: 'All'
          });
          setIsLoading(false);
          return;
        }
        
        // Priority 2: Fetch ticket and get event_name from ticket
        const ticket = await getTicket(listing.ticket_id);
        if ((ticket as any).event_name) {
          const eventName = (ticket as any).event_name;
          const foundEvent = events.find(e => e.title === eventName);
          if (foundEvent) {
            setEvent(foundEvent);
          } else {
            // Create minimal event for display
            setEvent({
              id: ticket.event_id?.toString() || '',
              title: eventName,
              description: '',
              date: '',
              location: '',
              imageUrl: '',
              price: 0,
              currency: 'ETH',
              totalTickets: 0,
              soldTickets: 0,
              organizer: '',
              category: 'All'
            });
          }
        } else {
          // Priority 3: Match by event_id
          const foundEvent = events.find(e => e.id === ticket.event_id?.toString());
          setEvent(foundEvent || null);
        }
      } catch (err) {
        console.error(`Failed to get ticket ${listing.ticket_id}:`, err);
        setEvent(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvent();
  }, [listing.ticket_id, listing.event_name, events]);

  if (isLoading) {
    return (
      <div className="group bg-background-elevated rounded-xl border border-border overflow-hidden">
        <div className="h-40 bg-background-hover animate-pulse" />
        <div className="p-5 space-y-4">
          <div className="h-6 bg-background-hover rounded animate-pulse" />
          <div className="h-4 bg-background-hover rounded animate-pulse" />
        </div>
      </div>
    );
  }

  const markupPercentage = listing.original_price && listing.original_price > 0
    ? ((listing.price - listing.original_price) / listing.original_price * 100).toFixed(1)
    : '0';

  return (
    <div className="group bg-background-elevated rounded-xl border border-border overflow-hidden card-hover">
      {event?.imageUrl && (
        <div className="h-40 relative overflow-hidden bg-background-hover">
          <img
            src={event.imageUrl}
            alt={event.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background-elevated to-transparent opacity-60" />
          <div className="absolute top-3 right-3 bg-background/80 backdrop-blur px-2 py-1 rounded border border-border text-xs font-mono text-foreground">
            {listing.price.toFixed(4)} ETH
          </div>
        </div>
      )}
      <div className="p-5 space-y-4">
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-primary uppercase tracking-wider bg-primary/10 px-2 py-1 rounded">
              {t('marketplace.resale')}
            </span>
            {listing.original_price && listing.original_price > 0 && (
              <span className="text-xs text-foreground-tertiary">
                {markupPercentage}% {t('marketplace.markup')}
              </span>
            )}
          </div>
          <h3 className="text-lg font-bold text-foreground group-hover:text-primary transition-colors">
            {listing.event_name || event?.title || `Ticket #${listing.ticket_id}`}
          </h3>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-foreground-secondary">{t('marketplace.resalePrice')}:</span>
            <span className="font-mono font-semibold text-foreground">{listing.price.toFixed(4)} ETH</span>
          </div>
          {listing.original_price && listing.original_price > 0 && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-foreground-tertiary">{t('marketplace.originalPrice')}:</span>
              <span className="text-foreground-tertiary line-through">{listing.original_price.toFixed(4)} ETH</span>
            </div>
          )}
          {event && (
            <>
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
            </>
          )}
        </div>

        <div className="pt-4 border-t border-border">
          <Link
            to={`/event/${event?.id || listing.ticket_id}`}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
          >
            {t('marketplace.viewListing')}
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </div>
  );
};


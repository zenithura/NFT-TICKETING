// File header: Event details page displaying event information and ticket purchase interface.
// Shows event description, pricing, availability, and allows users to mint NFT tickets.

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, ShieldCheck, ArrowLeft, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { getEvent, type EventResponse } from '../services/eventService';
import { Event } from '../types';
import { useWeb3 } from '../services/web3Context';
import { purchaseTickets } from '../services/ticketService';
import { EventDetailsSkeleton } from '../components/ui/TicketCardSkeleton';
import toast from 'react-hot-toast';
import { cn, formatCurrency } from '../lib/utils';

export const EventDetails: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const { isConnected, connectMetaMask, balance, address } = useWeb3();
  const [event, setEvent] = useState<Event | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isBuying, setIsBuying] = useState(false);
  const [ticketCount, setTicketCount] = useState(1);

  // Fetch event from API
  useEffect(() => {
    const fetchEvent = async () => {
      if (!id) {
        setError('Invalid event ID');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const eventId = parseInt(id, 10);
        if (isNaN(eventId)) {
          throw new Error('Invalid event ID');
        }

        const apiEvent: EventResponse = await getEvent(eventId);
        
        // Map API response to frontend Event interface
        const mappedEvent: Event = {
          id: apiEvent.id.toString(),
          title: apiEvent.name,
          description: apiEvent.description,
          date: apiEvent.date,
          location: apiEvent.location,
          imageUrl: apiEvent.image_url || 'https://picsum.photos/800/400?random=' + apiEvent.id,
          price: apiEvent.price,
          currency: (apiEvent.currency as 'ETH' | 'MATIC') || 'ETH',
          totalTickets: apiEvent.total_tickets,
          soldTickets: apiEvent.sold_tickets || 0,
          organizer: apiEvent.organizer_address || 'unknown',
          category: apiEvent.category || 'All',
        };
        
        setEvent(mappedEvent);
      } catch (err: any) {
        console.error('Failed to fetch event:', err);
        const errorMessage = err?.message || 'Failed to load event';
        setError(errorMessage);
        setEvent(null);
        // Don't show error toast for 404s - handled in UI
        if (err?.message && !err.message.includes('not found')) {
          // Could show toast notification here if needed
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvent();
  }, [id]);

  const handlePurchase = useCallback(async () => {
    if (!isConnected || !address) {
      toast.error(t('eventDetails.connectWalletToContinue'));
      try {
        await connectMetaMask();
      } catch (err) {
        // Connection failed, error already shown
      }
      return;
    }
    
    if (event.price > 0 && parseFloat(balance) < event.price * ticketCount) {
      toast.error(t('eventDetails.insufficientFunds'));
      return;
    }

    // Check if event has enough tickets available
    if (event.totalTickets - event.soldTickets < ticketCount) {
      toast.error(`Only ${event.totalTickets - event.soldTickets} tickets available`);
      return;
    }

    setIsBuying(true);

    try {
      // Purchase tickets - creates tickets in database
      const purchasedTickets = await purchaseTickets({
        event_id: parseInt(event.id, 10),
        owner_address: address,
        quantity: ticketCount,
        price: event.price,
      });

      toast.success(`${t('eventDetails.successfullyMinted')} ${ticketCount} ${t('eventDetails.tickets')}`);
      
      // Navigate to dashboard after a short delay to show success message
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (error: any) {
      console.error('Purchase error:', error);
      toast.error(error.message || 'Failed to purchase tickets. Please try again.');
    } finally {
      setIsBuying(false);
    }
  }, [isConnected, address, event, ticketCount, balance, connectMetaMask, navigate, t]);

  if (isLoading) {
    return <EventDetailsSkeleton />;
  }

  if (error || !event) {
    return (
      <div className="text-center py-20">
        <p className="text-foreground-secondary">{error || t('eventDetails.eventNotFound')}</p>
        <button
          onClick={() => navigate('/')}
          className="mt-4 text-primary hover:underline"
        >
          {t('eventDetails.backToMarketplace')}
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      {/* Toaster uses theme-aware styles from App.tsx - no need for duplicate Toaster */}

      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-foreground-secondary hover:text-foreground mb-6 transition-colors">
        <ArrowLeft size={16} /> {t('eventDetails.back')}
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Hero Image */}
          <div className="relative aspect-video rounded-2xl overflow-hidden border border-border">
            <img loading="lazy" src={event.imageUrl} alt={event.title} className="w-full h-full object-cover" />
            <div className="absolute top-4 left-4">
              <span className="px-3 py-1 rounded-full bg-background/60 backdrop-blur text-xs font-medium border border-border">
                {event.category}
              </span>
            </div>
          </div>

          <div className="space-y-6">
            <h1 className="text-4xl font-bold text-foreground tracking-tight">{event.title}</h1>

            <div className="flex flex-wrap gap-6 text-foreground-secondary pb-6 border-b border-border">
              <div className="flex items-center gap-2">
                <Calendar size={18} />
                <span>{new Date(event.date).toLocaleString(i18n.language === 'az' ? 'az-AZ' : 'en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin size={18} />
                <span>{event.location}</span>
              </div>
              <div className="flex items-center gap-2 text-success">
                <ShieldCheck size={18} />
                <span>{t('eventDetails.verified')}</span>
              </div>
            </div>

            <div className="max-w-none">
              <h2 className="text-xl font-bold mb-4 text-foreground">{t('eventDetails.about')}</h2>
              <p className="text-foreground-secondary leading-relaxed text-lg">{event.description}</p>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-24 bg-background-elevated border border-border rounded-xl p-6 space-y-6 shadow-2xl">
            <div>
              <p className="text-sm text-foreground-secondary mb-1">{t('eventDetails.currentPrice')}</p>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-foreground">{event.price}</span>
                <span className="text-lg font-medium text-foreground-tertiary mb-1">{event.currency}</span>
              </div>
            </div>

            <div className="p-4 bg-background-hover rounded-lg border border-border">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-foreground-secondary">{t('eventDetails.availability')}</span>
                <span className="text-foreground">{event.totalTickets - event.soldTickets} {t('eventDetails.left')}</span>
              </div>
              <div className="h-2 bg-background rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: `${(event.soldTickets / event.totalTickets) * 100}%` }}></div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between bg-background rounded-lg p-1 border border-border">
                <button
                  onClick={() => setTicketCount(Math.max(1, ticketCount - 1))}
                  className="w-10 h-10 flex items-center justify-center text-foreground-secondary hover:text-foreground hover:bg-background-hover rounded"
                >
                  -
                </button>
                <span className="font-bold">{ticketCount}</span>
                <button
                  onClick={() => setTicketCount(Math.min(10, ticketCount + 1))}
                  className="w-10 h-10 flex items-center justify-center text-foreground-secondary hover:text-foreground hover:bg-background-hover rounded"
                >
                  +
                </button>
              </div>

              <div className="space-y-2 pt-4 border-t border-border">
                <div className="flex justify-between text-sm text-foreground-secondary">
                  <span>{t('eventDetails.subtotal')}</span>
                  <span>{formatCurrency(event.price * ticketCount)}</span>
                </div>
                <div className="flex justify-between text-sm text-foreground-secondary">
                  <span>{t('eventDetails.fee')}</span>
                  <span>{formatCurrency(event.price * ticketCount * 0.02)}</span>
                </div>
                <div className="flex justify-between font-bold text-foreground pt-2">
                  <span>{t('eventDetails.total')}</span>
                  <span>{formatCurrency(event.price * ticketCount * 1.02)}</span>
                </div>
              </div>

              <button
                onClick={handlePurchase}
                disabled={isBuying}
                className="w-full bg-primary hover:bg-primary-hover text-white py-3 rounded-lg font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isBuying ? <Loader2 className="animate-spin" /> : t('eventDetails.mintTickets')}
              </button>

              <p className="text-xs text-center text-foreground-tertiary">
                {t('eventDetails.poweredBy')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

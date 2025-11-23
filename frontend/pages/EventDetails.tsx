import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, ShieldCheck, ArrowLeft, Loader2 } from 'lucide-react';
import { MOCK_EVENTS } from '../services/mockData';
import { useWeb3 } from '../services/web3Context';
import { EventDetailsSkeleton } from '../components/ui/TicketCardSkeleton';
import toast, { Toaster } from 'react-hot-toast';
import { cn, formatCurrency } from '../lib/utils';

export const EventDetails: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isConnected, connect, balance } = useWeb3();
  const [event, setEvent] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [isBuying, setIsBuying] = useState(false);
  const [ticketCount, setTicketCount] = useState(1);

  // Simulate loading delay - runs when id changes
  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      const foundEvent = MOCK_EVENTS.find(e => e.id === id);
      setEvent(foundEvent);
      setIsLoading(false);
    }, 600); // Reduced to 0.6 seconds

    return () => clearTimeout(timer);
  }, [id]);

  const handlePurchase = async () => {
    if (!isConnected) {
      toast.error('Connect wallet to continue');
      connect();
      return;
    }
    if (parseFloat(balance) < event.price * ticketCount) {
      toast.error('Insufficient funds');
      return;
    }
    setIsBuying(true);
    setTimeout(() => {
      toast.success(`Successfully minted ${ticketCount} tickets`);
      navigate('/dashboard');
    }, 2000);
  };

  if (isLoading) {
    return <EventDetailsSkeleton />;
  }

  if (!event) {
    return (
      <div className="text-center py-20">
        <p className="text-foreground-secondary">Event not found</p>
        <button
          onClick={() => navigate('/marketplace')}
          className="mt-4 text-primary hover:underline"
        >
          Back to Marketplace
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      <Toaster position="bottom-right" toastOptions={{
        style: { background: '#202020', color: '#EFEFEF', border: '1px solid #2F2F2F' }
      }} />

      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-foreground-secondary hover:text-foreground mb-6 transition-colors">
        <ArrowLeft size={16} /> Back
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Hero Image */}
          <div className="relative aspect-video rounded-2xl overflow-hidden border border-border">
            <img src={event.imageUrl} alt={event.title} className="w-full h-full object-cover" />
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
                <span>{new Date(event.date).toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin size={18} />
                <span>{event.location}</span>
              </div>
              <div className="flex items-center gap-2 text-success">
                <ShieldCheck size={18} />
                <span>Verified</span>
              </div>
            </div>

            <div className="prose prose-invert max-w-none">
              <h2 className="text-xl font-bold mb-4">About</h2>
              <p className="text-foreground-secondary leading-relaxed text-lg">{event.description}</p>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-24 bg-background-elevated border border-border rounded-xl p-6 space-y-6 shadow-2xl">
            <div>
              <p className="text-sm text-foreground-secondary mb-1">Current Price</p>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-foreground">{event.price}</span>
                <span className="text-lg font-medium text-foreground-tertiary mb-1">{event.currency}</span>
              </div>
            </div>

            <div className="p-4 bg-background-hover rounded-lg border border-border">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-foreground-secondary">Availability</span>
                <span className="text-foreground">{event.totalTickets - event.soldTickets} left</span>
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
                  <span>Subtotal</span>
                  <span>{formatCurrency(event.price * ticketCount)}</span>
                </div>
                <div className="flex justify-between text-sm text-foreground-secondary">
                  <span>Fee (2%)</span>
                  <span>{formatCurrency(event.price * ticketCount * 0.02)}</span>
                </div>
                <div className="flex justify-between font-bold text-foreground pt-2">
                  <span>Total</span>
                  <span>{formatCurrency(event.price * ticketCount * 1.02)}</span>
                </div>
              </div>

              <button
                onClick={handlePurchase}
                disabled={isBuying}
                className="w-full bg-primary hover:bg-primary-hover text-white py-3 rounded-lg font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isBuying ? <Loader2 className="animate-spin" /> : 'Mint Tickets'}
              </button>

              <p className="text-xs text-center text-foreground-tertiary">
                Powered by Polygon Network. Non-refundable.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

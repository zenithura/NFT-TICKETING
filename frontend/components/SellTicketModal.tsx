// File header: Modal component for selling tickets on the resale marketplace
// Allows buyers to list their tickets for resale with price validation (max 50% markup)

import React, { useState, useEffect } from 'react';
import { X, AlertCircle, DollarSign } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useWeb3 } from '../services/web3Context';
import { createResaleListing } from '../services/marketplaceService';
import { getTicket } from '../services/ticketService';
import { getEvent } from '../services/eventService';
import toast from 'react-hot-toast';
import { cn } from '../lib/utils';

interface SellTicketModalProps {
  isOpen: boolean;
  onClose: () => void;
  ticketId: number;
  eventId: number;
  originalPrice?: number;
}

export const SellTicketModal: React.FC<SellTicketModalProps> = ({
  isOpen,
  onClose,
  ticketId,
  eventId,
  originalPrice: propOriginalPrice,
}) => {
  const { t } = useTranslation();
  const { address } = useWeb3();
  const [resalePrice, setResalePrice] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [originalPrice, setOriginalPrice] = useState<number | null>(propOriginalPrice || null);
  const [maxPrice, setMaxPrice] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch ticket and event data to get original price
  useEffect(() => {
    if (isOpen && !propOriginalPrice) {
      const fetchData = async () => {
        try {
          const [ticket, event] = await Promise.all([
            getTicket(ticketId),
            getEvent(eventId),
          ]);
          
          // Try to get original price from ticket purchase_price, or event base_price
          const ticketPrice = (ticket as any).purchase_price || (ticket as any).price_paid;
          const eventPrice = event.price;
          const price = ticketPrice || eventPrice || 0;
          
          setOriginalPrice(price);
          setMaxPrice(price * 1.5); // 50% markup
        } catch (err) {
          console.error('Failed to fetch ticket/event data:', err);
          // Set defaults if fetch fails
          setOriginalPrice(0);
          setMaxPrice(null);
        }
      };
      
      fetchData();
    } else if (propOriginalPrice) {
      setOriginalPrice(propOriginalPrice);
      setMaxPrice(propOriginalPrice * 1.5);
    }
  }, [isOpen, ticketId, eventId, propOriginalPrice]);

  // Validate price on change
  useEffect(() => {
    if (resalePrice && originalPrice !== null && originalPrice > 0) {
      const price = parseFloat(resalePrice);
      const maxAllowed = originalPrice * 1.5;
      
      if (isNaN(price) || price <= 0) {
        setError(t('resale.invalidPrice'));
      } else if (price > maxAllowed) {
        setError(t('resale.priceTooHigh', { max: maxAllowed.toFixed(4) }));
      } else {
        setError(null);
      }
    } else if (resalePrice) {
      const price = parseFloat(resalePrice);
      if (isNaN(price) || price <= 0) {
        setError(t('resale.invalidPrice'));
      } else {
        setError(null);
      }
    } else {
      setError(null);
    }
  }, [resalePrice, originalPrice, t]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!address) {
      toast.error(t('resale.walletRequired'));
      return;
    }

    if (error) {
      return;
    }

    const price = parseFloat(resalePrice);
    if (isNaN(price) || price <= 0) {
      toast.error(t('resale.invalidPrice'));
      return;
    }

    // Final validation: 50% max markup
    if (originalPrice !== null && originalPrice > 0) {
      const maxAllowed = originalPrice * 1.5;
      if (price > maxAllowed) {
        toast.error(t('resale.priceTooHigh', { max: maxAllowed.toFixed(4) }));
        return;
      }
    }

    setIsLoading(true);
    try {
      await createResaleListing({
        ticket_id: ticketId,
        seller_address: address,
        price: price,
        original_price: originalPrice || undefined,
      });

      toast.success(t('resale.listingCreated'));
      onClose();
      setResalePrice('');
      // Refresh the page or update ticket list
      window.location.reload();
    } catch (err: any) {
      console.error('Failed to create listing:', err);
      toast.error(err.message || t('resale.createFailed'));
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const markupPercentage = originalPrice && originalPrice > 0 && resalePrice
    ? ((parseFloat(resalePrice) - originalPrice) / originalPrice * 100).toFixed(1)
    : '0';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-background-elevated rounded-xl border border-border shadow-2xl max-w-md w-full p-6 animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-foreground">{t('resale.sellTicket')}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-foreground-secondary hover:text-foreground hover:bg-background-hover transition-colors"
            aria-label={t('common.close')}
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Original Price Info */}
          {originalPrice !== null && originalPrice > 0 && (
            <div className="bg-background-hover p-4 rounded-lg border border-border">
              <div className="flex items-center justify-between text-sm">
                <span className="text-foreground-secondary">{t('resale.originalPrice')}:</span>
                <span className="font-mono font-semibold text-foreground">{originalPrice.toFixed(4)} ETH</span>
              </div>
              {maxPrice && (
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-foreground-secondary">{t('resale.maxPrice')}:</span>
                  <span className="font-mono font-semibold text-success">{maxPrice.toFixed(4)} ETH</span>
                </div>
              )}
            </div>
          )}

          {/* Price Input */}
          <div>
            <label htmlFor="resalePrice" className="block text-sm font-medium text-foreground mb-2">
              {t('resale.resalePrice')} (ETH) *
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
              <input
                id="resalePrice"
                type="number"
                step="0.0001"
                min="0"
                max={maxPrice || undefined}
                value={resalePrice}
                onChange={(e) => setResalePrice(e.target.value)}
                className={cn(
                  "w-full pl-10 pr-4 py-2.5 bg-background border rounded-lg",
                  "text-foreground placeholder-foreground-tertiary",
                  "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                  error ? "border-error" : "border-border"
                )}
                placeholder="0.0000"
                disabled={isLoading}
                required
              />
            </div>
            {error && (
              <p className="mt-1 text-sm text-error flex items-center gap-1">
                <AlertCircle size={14} />
                {error}
              </p>
            )}
            {originalPrice && originalPrice > 0 && resalePrice && !error && (
              <p className="mt-1 text-sm text-foreground-secondary">
                {t('resale.markup')}: {markupPercentage}%
              </p>
            )}
          </div>

          {/* Info Message */}
          <div className="bg-primary/10 border border-primary/20 rounded-lg p-3 text-sm text-foreground-secondary">
            <p>{t('resale.maxMarkupInfo')}</p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 rounded-lg border border-border text-foreground-secondary hover:text-foreground hover:border-foreground transition-colors disabled:opacity-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading || !!error || !resalePrice}
              className="flex-1 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('resale.creating') : t('resale.listTicket')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};


// File header: Create Event page for organizers to deploy new NFT ticket collections.
// Provides form for event details and ticket configuration with blockchain deployment.

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Upload, Loader2, AlertTriangle, Lock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import toast, { Toaster } from 'react-hot-toast';
import { useWeb3 } from '../services/web3Context';
import { useAuth } from '../services/authContext';
import { UserRole } from '../types';
import { createEvent, type CreateEventData } from '../services/eventService';

// Login required message component
const LoginRequiredMessage: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className="max-w-2xl mx-auto animate-slide-up">
      <div className="bg-background-elevated p-8 rounded-xl border border-border text-center">
        <Lock className="w-16 h-16 text-foreground-tertiary mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-foreground mb-2">{t('createEvent.loginRequired') || 'Login Required'}</h2>
        <p className="text-foreground-secondary mb-6">
          {t('createEvent.loginRequiredDesc') || 'Please log in as an organizer to create events.'}
        </p>
        <Link
          to="/login"
          className="inline-block bg-primary hover:bg-primary-hover text-white px-6 py-3 rounded-lg font-bold transition-all"
        >
          {t('common.login') || 'Login'}
        </Link>
      </div>
    </div>
  );
};

export const CreateEvent: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { userRole, isConnected } = useWeb3();
  const { isAuthenticated, user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<CreateEventData>({
    name: '',
    description: '',
    date: '',
    location: '',
    total_tickets: 100,
    price: 0.05,
    image_url: '',
    category: 'All',
    currency: 'ETH',
  });

  // Removed redirect logic - page will show login message instead

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'total_tickets' || name === 'price' ? parseFloat(value) || 0 : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.name.trim()) {
      toast.error('Event name is required');
      return;
    }
    if (!formData.description.trim()) {
      toast.error('Description is required');
      return;
    }
    if (!formData.date) {
      toast.error('Event date is required');
      return;
    }
    if (!formData.location.trim()) {
      toast.error('Location is required');
      return;
    }
    if (formData.total_tickets <= 0) {
      toast.error('Total tickets must be greater than 0');
      return;
    }
    if (formData.price < 0) {
      toast.error('Price cannot be negative');
      return;
    }

    if (!isAuthenticated) {
      toast.error('Please login to create events');
      navigate('/login');
      return;
    }

    setIsSubmitting(true);
    setApiError(null);

    try {
      // Format date to ISO string
      const eventDate = new Date(formData.date);
      if (isNaN(eventDate.getTime())) {
        throw new Error('Invalid date format');
      }

      const eventData: CreateEventData = {
        ...formData,
        date: eventDate.toISOString(),
      };

      await createEvent(eventData);
      toast.success(t('createEvent.eventContractDeployed') || 'Event created successfully!');
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (error: any) {
      console.error('Error creating event:', error);
      const errorMessage = error?.message || error?.toString() || 'Failed to create event. Please try again.';
      setApiError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show login message if not authenticated or not organizer/admin
  const canCreateEvents = isAuthenticated && (userRole === UserRole.ORGANIZER || userRole === UserRole.ADMIN);
  const isSubmitDisabled = !canCreateEvents || isSubmitting;

  if (!canCreateEvents) {
    return <LoginRequiredMessage />;
  }

  return (
    <div className="max-w-2xl mx-auto animate-slide-up" data-cy="create-event-page">
      <Toaster position="bottom-right" />

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">{t('createEvent.title')}</h1>
        <p className="text-foreground-secondary">{t('createEvent.subtitle')}</p>
      </div>

      {apiError && (
        <div className="mb-6 bg-error/10 border border-error/20 rounded-lg p-4 text-error">
          <AlertTriangle className="inline w-5 h-5 mr-2" />
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8" data-cy="create-event-form">
        {/* Section 1 */}
        <div className="bg-background-elevated p-6 rounded-xl border border-border space-y-6">
          <h2 className="text-lg font-semibold text-foreground border-b border-border pb-2">{t('createEvent.basicDetails')}</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">{t('createEvent.eventName')}</label>
              <input
                required
                type="text"
                name="name"
                data-cy="event-name-input"
                value={formData.name}
                onChange={handleChange}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary focus:ring-0 transition-colors"
                placeholder={t('createEvent.eventNamePlaceholder')}
              />
            </div>

            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">{t('createEvent.description')}</label>
              <textarea
                required
                rows={3}
                name="description"
                data-cy="event-description-input"
                value={formData.description}
                onChange={handleChange}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary focus:ring-0 transition-colors"
                placeholder={t('createEvent.descriptionPlaceholder')}
              />
            </div>

            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">Event Date & Time</label>
              <input
                required
                type="datetime-local"
                name="date"
                value={formData.date}
                onChange={handleChange}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">Location</label>
              <input
                required
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary transition-colors"
                placeholder="e.g. San Francisco, CA or Venue Name, City"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-foreground-secondary mb-1.5">{t('createEvent.category')}</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary transition-colors"
                >
                  <option value="All">All</option>
                  <option value="Music">{t('createEvent.categories.music')}</option>
                  <option value="Technology">{t('createEvent.categories.technology')}</option>
                  <option value="Art">{t('createEvent.categories.art')}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-foreground-secondary mb-1.5">{t('createEvent.coverImage')} (URL)</label>
                <input
                  type="url"
                  name="image_url"
                  value={formData.image_url}
                  onChange={handleChange}
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary transition-colors"
                  placeholder="https://example.com/image.jpg"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 2 */}
        <div className="bg-background-elevated p-6 rounded-xl border border-border space-y-6">
          <h2 className="text-lg font-semibold text-foreground border-b border-border pb-2">{t('createEvent.ticketConfiguration')}</h2>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">{t('createEvent.totalSupply')}</label>
              <input
                required
                type="number"
                name="totalSupply"
                data-cy="event-total-supply-input"
                value={formData.total_tickets}
                onChange={(e) => {
                  const value = e.target.value;
                  setFormData(prev => ({
                    ...prev,
                    total_tickets: parseFloat(value) || 0
                  }));
                }}
                min="1"
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary"
                placeholder={t('createEvent.totalSupplyPlaceholder')}
              />
            </div>
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">{t('createEvent.priceETH')}</label>
              <input
                required
                type="number"
                name="ticketPrice"
                data-cy="event-ticket-price-input"
                value={formData.price}
                onChange={(e) => {
                  const value = e.target.value;
                  setFormData(prev => ({
                    ...prev,
                    price: parseFloat(value) || 0
                  }));
                }}
                step="0.01"
                min="0"
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary"
                placeholder={t('createEvent.priceETHPlaceholder')}
              />
            </div>
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">Currency</label>
              <select
                name="currency"
                value={formData.currency}
                onChange={handleChange}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary"
              >
                <option value="ETH">ETH</option>
                <option value="MATIC">MATIC</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>

          <div className="bg-primary/5 border border-primary/10 rounded p-3 flex gap-3 items-start">
            <AlertTriangle className="text-primary shrink-0 mt-0.5" size={16} />
            <p className="text-xs text-foreground-secondary">{t('createEvent.warning')}</p>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            data-cy="submit-event-form"
            disabled={isSubmitDisabled}
            className="bg-primary hover:bg-primary-hover text-white px-8 py-3 rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : t('createEvent.deployContract')}
          </button>
        </div>
      </form>
    </div>
  );
};

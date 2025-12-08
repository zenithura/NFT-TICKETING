/**
 * SWR configuration for API caching and data fetching
 * Provides automatic caching, revalidation, and error handling
 */

import useSWR, { SWRConfiguration } from 'swr';
import { authenticatedFetch } from './authService';
import { getUserTickets } from './ticketService';
import type { Ticket } from '../types';

// Use relative URL when proxying, or full URL if VITE_API_URL is set
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Default SWR configuration
export const swrConfig: SWRConfiguration = {
  revalidateOnFocus: false, // Don't revalidate on window focus (better performance)
  revalidateOnReconnect: true, // Revalidate when network reconnects
  dedupingInterval: 2000, // Dedupe requests within 2 seconds
  focusThrottleInterval: 5000, // Throttle focus revalidation
  errorRetryCount: 2, // Retry failed requests 2 times
  errorRetryInterval: 1000, // Wait 1 second between retries
  keepPreviousData: true, // Keep previous data while fetching new data
  refreshInterval: 0, // Disable automatic polling (can be enabled per hook)
};

// Fetcher function for SWR
export const fetcher = async (url: string) => {
  const response = await authenticatedFetch(url);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch' }));
    throw new Error(error.detail || 'Failed to fetch');
  }
  return response.json();
};

// Custom hook for events with caching
export const useEvents = () => {
  return useSWR<import('./eventService').EventResponse[]>(
    '/events/',
    fetcher,
    {
      ...swrConfig,
      refreshInterval: 30000, // Refresh every 30 seconds
      // Don't block render - return undefined immediately
      revalidateOnMount: true,
      // Show stale data immediately if available
      keepPreviousData: true,
    }
  );
};

// Custom hook for single event with caching
export const useEvent = (eventId: number | null) => {
  return useSWR<import('./eventService').EventResponse>(
    eventId ? `/events/${eventId}` : null,
    fetcher,
    swrConfig
  );
};

// Custom hook for resale listings with caching
export const useResaleListings = () => {
  return useSWR<import('./marketplaceService').ResaleListing[]>(
    '/marketplace/?status=active',
    fetcher,
    {
      ...swrConfig,
      refreshInterval: 20000, // Refresh every 20 seconds
    }
  );
};

// Custom hook for user tickets with caching
// IMPORTANT: Use getUserTickets to get properly mapped tickets with eventName
export const useUserTickets = (address: string | null) => {
  return useSWR<Ticket[]>(
    address ? `tickets:user:${address}` : null, // Use custom key
    async () => {
      if (!address) return null;
      return getUserTickets(address); // Use the mapping function that adds eventName!
    },
    {
      ...swrConfig,
      refreshInterval: 0, // Don't auto-refresh user tickets (user action required)
    }
  );
};

// Mutate function to invalidate cache
export { mutate } from 'swr';


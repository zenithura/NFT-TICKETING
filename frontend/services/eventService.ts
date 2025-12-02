/**
 * Event service for creating and managing events
 */

import { authenticatedFetch } from './authService';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface CreateEventData {
  name: string;
  description: string;
  date: string; // ISO format
  location: string;
  total_tickets: number;
  price: number;
  image_url?: string;
  category?: string;
  currency?: string;
}

export interface EventResponse {
  id: number;
  name: string;
  description: string;
  date: string;
  location: string;
  total_tickets: number;
  price: number;
  organizer_address: string;
  image_url?: string;
  category?: string;
  currency?: string;
  created_at: string;
  sold_tickets: number;
}

/**
 * Create a new event
 */
export const createEvent = async (eventData: CreateEventData): Promise<EventResponse> => {
  const response = await authenticatedFetch('/events/', {
    method: 'POST',
    body: JSON.stringify(eventData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create event');
  }

  return response.json();
};

/**
 * Get all events
 */
export const getEvents = async (): Promise<EventResponse[]> => {
  const response = await authenticatedFetch('/events/');

  if (!response.ok) {
    throw new Error('Failed to fetch events');
  }

  return response.json();
};

/**
 * Get event by ID
 */
export const getEvent = async (eventId: number): Promise<EventResponse> => {
  const response = await authenticatedFetch(`/events/${eventId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch event');
  }

  return response.json();
};

/**
 * Get organizer statistics
 */
export interface OrganizerStats {
  total_revenue: number;
  tickets_sold: number;
  active_events: number;
  total_events: number;
}

export const getOrganizerStats = async (organizerAddress: string): Promise<OrganizerStats> => {
  const response = await authenticatedFetch(`/events/organizer/${organizerAddress}/stats`);

  if (!response.ok) {
    throw new Error('Failed to fetch organizer stats');
  }

  return response.json();
};


/**
 * Event service for creating and managing events
 */

import { authenticatedFetch } from './authService';

// Use relative URL when proxying, or full URL if VITE_API_URL is set
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '/api';

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
 * Create a new event with robust error handling
 */
export const createEvent = async (eventData: CreateEventData): Promise<EventResponse> => {
  try {
    const response = await authenticatedFetch('/events/', {
      method: 'POST',
      body: JSON.stringify(eventData),
    });

    if (!response.ok) {
      let errorMessage = 'Failed to create event';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // If response is not JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }
      
      if (response.status === 400) {
        throw new Error(`Invalid event data: ${errorMessage}`);
      } else if (response.status === 401) {
        throw new Error('Authentication required. Please login again.');
      } else if (response.status === 403) {
        throw new Error('You do not have permission to create events.');
      } else if (response.status === 500) {
        throw new Error(`Server error: ${errorMessage}. Please try again later.`);
      } else {
        throw new Error(errorMessage);
      }
    }

    return await response.json();
  } catch (error) {
    // Re-throw if it's already an Error
    if (error instanceof Error) {
      throw error;
    }
    // Handle network errors and other exceptions
    if (error && typeof error === 'object' && 'message' in error) {
      throw new Error(String(error.message) || 'Failed to create event');
    }
    throw new Error('An unexpected error occurred while creating the event. Please try again.');
  }
};

/**
 * Get all events with robust error handling
 */
export const getEvents = async (): Promise<EventResponse[]> => {
  try {
    const response = await authenticatedFetch('/events/');

    if (!response.ok) {
      let errorMessage = 'Failed to fetch events';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = response.statusText || errorMessage;
      }
      
      if (response.status === 500) {
        throw new Error(`Server error: ${errorMessage}. Please try again later.`);
      } else {
        throw new Error(errorMessage);
      }
    }

    const events = await response.json();
    
    // Debug: Log raw events from API
    console.log('🎪 Raw events from API:', events.map((e: EventResponse) => ({
      id: e.id,
      id_type: typeof e.id,
      name: e.name
    })));
    
    return events;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('An unexpected error occurred while fetching events. Please try again.');
  }
};

/**
 * Get event by ID with improved error handling
 */
export const getEvent = async (eventId: number): Promise<EventResponse> => {
  try {
    const response = await authenticatedFetch(`/events/${eventId}`);

    if (!response.ok) {
      let errorMessage = 'Failed to fetch event';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // If response is not JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }
      
      if (response.status === 404) {
        throw new Error(`Event with ID ${eventId} not found`);
      } else if (response.status === 500) {
        throw new Error(`Server error: ${errorMessage}. Please try again later.`);
      } else {
        throw new Error(errorMessage);
      }
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('An unexpected error occurred while fetching the event');
  }
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


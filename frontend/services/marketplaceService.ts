/**
 * Marketplace service for resale listings
 */

import { authenticatedFetch } from './authService';

export interface ResaleListing {
  id: number;
  ticket_id: number;
  seller_address: string;
  price: number;
  original_price?: number;
  status: 'active' | 'sold' | 'cancelled';
  created_at: string;
  event_name?: string;  // Event name from backend
}

export interface CreateResaleListingRequest {
  ticket_id: number;
  seller_address: string;
  price: number;
  original_price?: number;
}

/**
 * Create a resale listing for a ticket
 */
export const createResaleListing = async (request: CreateResaleListingRequest): Promise<ResaleListing> => {
  const response = await authenticatedFetch('/marketplace/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ticket_id: request.ticket_id,
      seller_address: request.seller_address,
      price: request.price,
      original_price: request.original_price,
      status: 'active',
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create resale listing');
  }

  return response.json();
};

/**
 * Get all active resale listings
 */
export const getResaleListings = async (): Promise<ResaleListing[]> => {
  const response = await authenticatedFetch('/marketplace/?status=active');

  if (!response.ok) {
    throw new Error('Failed to fetch resale listings');
  }

  return response.json();
};

/**
 * Get a specific resale listing
 */
export const getResaleListing = async (listingId: number): Promise<ResaleListing> => {
  const response = await authenticatedFetch(`/marketplace/${listingId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch resale listing');
  }

  return response.json();
};

/**
 * Buy a ticket from resale
 */
export const buyResaleTicket = async (listingId: number, buyerAddress: string): Promise<{ message: string; ticket: any; listing: any }> => {
  const response = await authenticatedFetch(`/marketplace/${listingId}/buy`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      buyer_address: buyerAddress,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to purchase ticket');
  }

  return response.json();
};


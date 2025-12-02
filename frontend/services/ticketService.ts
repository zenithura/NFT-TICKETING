/**
 * Ticket service for fetching and managing user tickets
 */

import { authenticatedFetch } from './authService';

export interface TicketResponse {
  id: number;
  event_id: number;
  owner_address: string;
  status: 'available' | 'used' | 'transferred' | 'resale_listed';
  nft_token_id?: number;
  purchase_date?: string;
  price_paid?: number;
  qr_code_data?: string;
  created_at: string;
}

// Ticket interface matches the one in types.ts - using import instead
import type { Ticket } from '../types';

export interface PurchaseTicketRequest {
  event_id: number;
  owner_address: string;
  quantity: number;
  price: number;
}

/**
 * Purchase tickets for an event
 */
export const purchaseTickets = async (request: PurchaseTicketRequest): Promise<TicketResponse[]> => {
  const tickets: TicketResponse[] = [];
  
  // Create multiple tickets (one for each quantity)
  for (let i = 0; i < request.quantity; i++) {
    const response = await authenticatedFetch('/tickets/', {
      method: 'POST',
      body: JSON.stringify({
        event_id: request.event_id,
        owner_address: request.owner_address,
        status: 'available',
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to create ticket ${i + 1} of ${request.quantity}`);
    }

    const ticket: TicketResponse = await response.json();
    tickets.push(ticket);
  }

  return tickets;
};

/**
 * Get all tickets owned by a user
 */
export const getUserTickets = async (ownerAddress: string): Promise<Ticket[]> => {
  const response = await authenticatedFetch(`/tickets/user/${ownerAddress}`);

  if (!response.ok) {
    throw new Error('Failed to fetch tickets');
  }

  const apiTickets: TicketResponse[] = await response.json();
  
  // Map API response to frontend Ticket interface
  return apiTickets.map((t: TicketResponse) => ({
    id: t.id.toString(),
    eventId: t.event_id.toString(),
    tokenId: t.nft_token_id?.toString() || t.id.toString(),
    ownerAddress: t.owner_address,
    purchaseDate: t.purchase_date || t.created_at,
    status: mapTicketStatus(t.status),
    pricePaid: t.price_paid || 0,
    qrCodeData: t.qr_code_data || `ticket_${t.id}_${t.nft_token_id || t.id}`,
  }));
};

/**
 * Get all tickets for a specific event
 */
export const getEventTickets = async (eventId: number): Promise<TicketResponse[]> => {
  const response = await authenticatedFetch(`/tickets/event/${eventId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch event tickets');
  }

  return response.json();
};

/**
 * Get a specific ticket by ID
 */
export const getTicket = async (ticketId: number): Promise<TicketResponse> => {
  const response = await authenticatedFetch(`/tickets/${ticketId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch ticket');
  }

  return response.json();
};

/**
 * Validate a ticket (for scanner)
 */
export const validateTicket = async (ticketId: number): Promise<{ valid: boolean; message: string }> => {
  const response = await authenticatedFetch(`/tickets/${ticketId}`);

  if (!response.ok) {
    return { valid: false, message: 'Ticket not found' };
  }

  const ticket: TicketResponse = await response.json();
  
  if (ticket.status === 'used') {
    return { valid: false, message: 'Ticket already used' };
  }
  
  if (ticket.status === 'available') {
    return { valid: true, message: `Ticket #${ticket.nft_token_id || ticket.id} - Valid - Owner: ${ticket.owner_address.slice(0, 6)}...${ticket.owner_address.slice(-4)}` };
  }
  
  return { valid: false, message: 'Invalid ticket status' };
};

/**
 * Mark a ticket as used
 */
export const useTicket = async (ticketId: number): Promise<void> => {
  const response = await authenticatedFetch(`/tickets/${ticketId}/use`, {
    method: 'PATCH',
  });

  if (!response.ok) {
    throw new Error('Failed to mark ticket as used');
  }
};

/**
 * Map backend ticket status to frontend status
 */
function mapTicketStatus(status: string): 'VALID' | 'USED' | 'RESALE_LISTED' {
  switch (status) {
    case 'available':
      return 'VALID';
    case 'used':
      return 'USED';
    case 'resale_listed':
      return 'RESALE_LISTED';
    default:
      return 'VALID';
  }
}

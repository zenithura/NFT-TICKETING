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
  event_name?: string;  // Event name from backend - THIS FIELD EXISTS IN API RESPONSE!
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
        purchase_price: request.price, // Store purchase price for resale markup validation
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
  
  // CRITICAL: Verify event_name is in the response
  console.log('🔵 API RESPONSE CHECK:', apiTickets.map(t => {
    const raw = t as any;
    const hasEventName = 'event_name' in raw;
    return {
      id: t.id,
      event_id: raw.event_id,
      has_event_name_key: hasEventName,
      event_name_value: raw.event_name,
      all_keys: Object.keys(raw).sort()
    };
  }));
  
  // Debug: Log raw API response with full object inspection
  console.log('🎫 Raw tickets from API (full):', JSON.stringify(apiTickets, null, 2));
  console.log('🎫 Raw tickets from API (summary):', apiTickets.map(t => {
    const raw = t as any;
    return {
      id: t.id,
      event_id: raw.event_id,
      event_id_type: typeof raw.event_id,
      event_name: raw.event_name,
      event_name_type: typeof raw.event_name,
      all_keys: Object.keys(raw),
      owner_address: t.owner_address
    };
  }));
  
  // Map API response to frontend Ticket interface
  // Show all tickets, even if event_id is 0 or missing
  const mappedTickets = apiTickets.map((t: TicketResponse) => {
    // Get raw object to access all properties (bypass TypeScript)
    const raw = t as any;
    
    // Get event_id - try multiple ways to access it
    const rawEventId = raw.event_id !== undefined ? raw.event_id : (t.event_id !== undefined ? t.event_id : undefined);
    
    // Convert event_id to string - tickets have event_id from database (e.g., 6, 4)
    let eventId: string | undefined;
    
    // Handle event_id conversion - be very explicit
    if (rawEventId != null && rawEventId !== undefined && rawEventId !== 'undefined') {
      // Try to convert to number
      const numValue = typeof rawEventId === 'number' ? rawEventId : Number(rawEventId);
      if (!isNaN(numValue) && isFinite(numValue)) {
        if (numValue === 0) {
          eventId = '0';
        } else {
          eventId = String(numValue);
        }
      }
    }
    
    const tokenId = t.nft_token_id != null ? t.nft_token_id.toString() : (t.id ? t.id.toString() : undefined);
    
    // Get event_name from response - The API returns "event_name" (snake_case)
    // We confirmed with curl that backend returns: "event_name": "BEU INHA 2023"
    // Access it directly from the raw object
    const eventName = raw.event_name || t.event_name || undefined;
    
    // Ensure eventName is a valid non-empty string
    const finalEventName = (eventName && typeof eventName === 'string' && eventName.trim().length > 0) 
      ? eventName.trim() 
      : undefined;
    
    const mapped = {
      id: t.id ? t.id.toString() : 'unknown',
      eventId: eventId, // Will be "6", "4", "0", or undefined
      tokenId: tokenId || t.id?.toString() || 'unknown',
      ownerAddress: t.owner_address || 'unknown',
      purchaseDate: t.purchase_date || t.created_at || new Date().toISOString(),
      status: mapTicketStatus(t.status || 'available'),
      pricePaid: t.price_paid || 0,
      qrCodeData: t.qr_code_data || `ticket_${t.id}_${t.nft_token_id || t.id}`,
      eventName: finalEventName, // Event name from backend - THIS IS WHAT WE NEED!
    };
    
    console.log(`🎫 Mapped ticket ${mapped.id}:`, {
      eventId: mapped.eventId,
      eventName: mapped.eventName,
      raw_event_id: rawEventId,
      raw_event_id_type: typeof rawEventId,
      raw_event_name: raw.event_name,
      finalEventName: finalEventName,
      hasEventName: !!mapped.eventName,
      hasEventId: !!mapped.eventId
    });
    return mapped;
  });
  
  // Final verification - log all mapped tickets with eventName
  console.log('✅ FINAL MAPPED TICKETS:', mappedTickets.map(t => ({
    id: t.id,
    eventId: t.eventId,
    eventName: t.eventName,
    hasEventName: !!t.eventName,
    eventNameType: typeof t.eventName
  })));
  
  return mappedTickets;
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

export enum UserRole {
  BUYER = 'BUYER',
  ORGANIZER = 'ORGANIZER',
  RESELLER = 'RESELLER',
  SCANNER = 'SCANNER',
  ADMIN = 'ADMIN'
}

export interface Event {
  id: string;
  title: string;
  description: string;
  date: string;
  location: string;
  imageUrl: string;
  price: number;
  currency: 'ETH' | 'MATIC';
  totalTickets: number;
  soldTickets: number;
  organizer: string;
  category: string;
}

export interface Ticket {
  id: string;
  eventId: string;
  tokenId: string;
  ownerAddress: string;
  purchaseDate: string;
  status: 'VALID' | 'USED' | 'RESALE_LISTED';
  pricePaid: number;
  qrCodeData: string;
  eventName?: string;  // Event name from backend (if available)
}

export interface AnalyticsData {
  name: string;
  sales: number;
  revenue: number;
}

export interface ResaleListing {
  id: string;
  ticketId: string;
  eventId: string;
  seller: string;
  price: number;
  originalPrice: number;
}
import { Event, Ticket, ResaleListing } from '../types';

export const MOCK_EVENTS: Event[] = [
  {
    id: '1',
    title: 'Crypto Art Gala 2024',
    description: 'An exclusive evening celebrating the best in digital art and NFTs. Meet the artists and collectors shaping the future.',
    date: '2024-11-15T19:00:00',
    location: 'Metaverse Convention Center, Decentraland',
    imageUrl: 'https://picsum.photos/800/400?random=1',
    price: 0.05,
    currency: 'ETH',
    totalTickets: 1000,
    soldTickets: 850,
    organizer: '0x123...abc',
    category: 'Art'
  },
  {
    id: '2',
    title: 'Web3 Developer Summit',
    description: 'The biggest gathering of blockchain developers. Workshops, keynotes, and hacking sessions.',
    date: '2024-12-05T09:00:00',
    location: 'San Francisco, CA',
    imageUrl: 'https://picsum.photos/800/400?random=2',
    price: 0.15,
    currency: 'ETH',
    totalTickets: 500,
    soldTickets: 120,
    organizer: '0x456...def',
    category: 'Technology'
  },
  {
    id: '3',
    title: 'Neon Nights Music Festival',
    description: 'A cyberpunk themed electronic music festival featuring top DJs from around the globe.',
    date: '2025-01-20T20:00:00',
    location: 'Tokyo, Japan',
    imageUrl: 'https://picsum.photos/800/400?random=3',
    price: 0.08,
    currency: 'ETH',
    totalTickets: 5000,
    soldTickets: 4500,
    organizer: '0x789...ghi',
    category: 'Music'
  }
];

export const MOCK_MY_TICKETS: Ticket[] = [
  {
    id: 't1',
    eventId: '1',
    tokenId: '1042',
    ownerAddress: '0xUser',
    purchaseDate: '2024-10-01',
    status: 'VALID',
    pricePaid: 0.05,
    qrCodeData: 'valid_ticket_1042_sig_xyz'
  },
  {
    id: 't2',
    eventId: '3',
    tokenId: '305',
    ownerAddress: '0xUser',
    purchaseDate: '2024-09-15',
    status: 'RESALE_LISTED',
    pricePaid: 0.08,
    qrCodeData: 'valid_ticket_305_sig_abc'
  }
];

export const MOCK_RESALE: ResaleListing[] = [
  {
    id: 'r1',
    ticketId: 't99',
    eventId: '3',
    seller: '0xOtherUser',
    price: 0.09, // Slightly higher
    originalPrice: 0.08
  }
];
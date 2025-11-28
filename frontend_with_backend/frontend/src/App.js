import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { Calendar, MapPin, Ticket, Wallet as WalletIcon, ShoppingCart, ScanLine, Plus } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

// Ensure the backend URL is properly formatted
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
  ? process.env.REACT_APP_BACKEND_URL.replace(/([^:])\/+$/, '$1') // Remove trailing slashes but keep ://
  : 'http://localhost:8000';
const API = `${BACKEND_URL}${BACKEND_URL.endsWith('/') ? '' : '/'}api`;

// Configure axios
axios.defaults.timeout = 10000;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Log all requests
axios.interceptors.request.use(
  config => {
    console.log("API Request:", config.method.toUpperCase(), config.url);
    return config;
  },
  error => Promise.reject(error)
);

// Log all responses
axios.interceptors.response.use(
  response => {
    console.log("API Response:", response.status, response.config.url);
    return response;
  },
  error => {
    console.error("API Error:", {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      url: error.config?.url,
      method: error.config?.method
    });
    return Promise.reject(error);
  }
);

// Wallet Context
const WalletContext = ({ children }) => {
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const savedWallet = localStorage.getItem('wallet_address');
    if (savedWallet) {
      connectWallet(savedWallet);
    }
  }, []);

  const connectWallet = async (address) => {
    setLoading(true);
    try {
      console.log("Connecting wallet to:", `${API}/wallet/connect`);
      const response = await axios.post(`${API}/wallet/connect`, { address });
      setWallet(response.data);
      localStorage.setItem('wallet_address', address);
      toast.success("Wallet connected successfully");
    } catch (error) {
      console.error("Error connecting wallet:", error);
      const errorMsg = error.response?.data?.detail || error.message || "Failed to connect wallet";
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const disconnectWallet = () => {
    setWallet(null);
    localStorage.removeItem('wallet_address');
    toast.info("Wallet disconnected");
  };

  const refreshWallet = async () => {
    if (!wallet) return;
    try {
      const response = await axios.get(`${API}/wallet/${wallet.address}`);
      setWallet(response.data);
    } catch (error) {
      console.error("Error refreshing wallet:", error);
    }
  };

  return children({ wallet, connectWallet, disconnectWallet, refreshWallet, loading });
};

// Header Component
const Header = ({ wallet, onConnect, onDisconnect }) => {
  const [showConnectDialog, setShowConnectDialog] = useState(false);
  const [walletAddress, setWalletAddress] = useState("");

  const handleConnect = () => {
    if (!walletAddress) {
      toast.error("Please enter a wallet address");
      return;
    }
    onConnect(walletAddress);
    setShowConnectDialog(false);
    setWalletAddress("");
  };

  const generateRandomWallet = () => {
    const chars = '0123456789abcdef';
    let address = '0x';
    for (let i = 0; i < 40; i++) {
      address += chars[Math.floor(Math.random() * chars.length)];
    }
    setWalletAddress(address);
  };

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link to="/" className="flex items-center space-x-2">
            <Ticket className="h-6 w-6" />
            <span className="text-xl font-bold">NFT Tickets</span>
          </Link>

          <nav className="hidden md:flex items-center space-x-6">
            <Link to="/" className="text-sm font-medium hover:text-primary transition-colors" data-testid="nav-events">
              Events
            </Link>
            <Link to="/marketplace" className="text-sm font-medium hover:text-primary transition-colors" data-testid="nav-marketplace">
              Marketplace
            </Link>
            {wallet && (
              <Link to="/my-tickets" className="text-sm font-medium hover:text-primary transition-colors" data-testid="nav-my-tickets">
                My Tickets
              </Link>
            )}
            <Link to="/create-event" className="text-sm font-medium hover:text-primary transition-colors" data-testid="nav-create-event">
              Create Event
            </Link>
          </nav>

          <div className="flex items-center space-x-4">
            {wallet ? (
              <div className="flex items-center space-x-3">
                <div className="text-sm" data-testid="wallet-balance">
                  <div className="font-medium">{wallet.balance.toFixed(2)} ETH</div>
                  <div className="text-xs text-muted-foreground">{wallet.address.slice(0, 6)}...{wallet.address.slice(-4)}</div>
                </div>
                <Button variant="outline" size="sm" onClick={onDisconnect} data-testid="disconnect-wallet-btn">
                  Disconnect
                </Button>
              </div>
            ) : (
              <Button onClick={() => setShowConnectDialog(true)} data-testid="connect-wallet-btn">
                <WalletIcon className="mr-2 h-4 w-4" />
                Connect Wallet
              </Button>
            )}
          </div>
        </div>
      </header>

      <Dialog open={showConnectDialog} onOpenChange={setShowConnectDialog}>
        <DialogContent data-testid="connect-wallet-dialog">
          <DialogHeader>
            <DialogTitle>Connect Wallet</DialogTitle>
            <DialogDescription>
              Enter your wallet address or generate a random one for testing.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="wallet-address">Wallet Address</Label>
              <Input
                id="wallet-address"
                placeholder="0x..."
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                data-testid="wallet-address-input"
              />
            </div>
            <Button variant="outline" onClick={generateRandomWallet} className="w-full" data-testid="generate-wallet-btn">
              Generate Random Wallet
            </Button>
          </div>
          <DialogFooter>
            <Button onClick={handleConnect} data-testid="confirm-connect-btn">Connect</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

// Events Page
const EventsPage = ({ wallet, refreshWallet }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      console.log("Fetching events from:", `${API}/events`);
      const response = await axios.get(`${API}/events`);
      console.log("Events fetched successfully:", response.data);
      setEvents(response.data);
    } catch (error) {
      console.error("Error fetching events:", error);
      const errorMsg = error.response?.data?.detail || error.message || "Failed to load events";
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleBuyTicket = async (event) => {
    if (!wallet) {
      toast.error("Please connect your wallet first");
      return;
    }

    try {
      await axios.post(`${API}/tickets/mint`, {
        event_id: event.event_id,
        buyer_address: wallet.address
      });
      toast.success(`Ticket purchased for ${event.name}!`);
      await refreshWallet();
      fetchEvents();
    } catch (error) {
      console.error("Error buying ticket:", error);
      toast.error(error.response?.data?.detail || "Failed to purchase ticket");
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading events...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Upcoming Events</h1>
        <p className="text-muted-foreground">Discover and purchase NFT tickets for exclusive events</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {events.map((event) => (
          <Card key={event.event_id} className="overflow-hidden hover:shadow-lg transition-shadow" data-testid={`event-card-${event.event_id}`}>
            <div className="h-48 bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
              <Ticket className="h-20 w-20 text-slate-400" />
            </div>
            <CardHeader>
              <div className="flex items-center justify-between mb-2">
                <Badge variant={event.status === 'ACTIVE' ? 'default' : 'secondary'} data-testid={`event-status-${event.event_id}`}>
                  {event.status}
                </Badge>
                <span className="text-lg font-bold" data-testid={`event-price-${event.event_id}`}>{event.base_price} ETH</span>
              </div>
              <CardTitle data-testid={`event-name-${event.event_id}`}>{event.name}</CardTitle>
              <CardDescription>
                <div className="flex items-center space-x-4 mt-2 text-sm">
                  <div className="flex items-center">
                    <Calendar className="mr-1 h-4 w-4" />
                    {new Date(event.event_date).toLocaleDateString()}
                  </div>
                  <div className="flex items-center">
                    <Ticket className="mr-1 h-4 w-4" />
                    {event.available_tickets} tickets
                  </div>
                </div>
              </CardDescription>
            </CardHeader>
            <CardFooter>
              <Button
                className="w-full"
                onClick={() => handleBuyTicket(event)}
                disabled={event.status !== 'ACTIVE'}
                data-testid={`buy-ticket-btn-${event.event_id}`}
              >
                <ShoppingCart className="mr-2 h-4 w-4" />
                Buy Ticket
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {events.length === 0 && (
        <div className="text-center py-12">
          <Ticket className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No events available</h3>
          <p className="text-muted-foreground">Check back later for upcoming events</p>
        </div>
      )}
    </div>
  );
};

// Marketplace Page
const MarketplacePage = ({ wallet, refreshWallet }) => {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchListings();
  }, []);

  const fetchListings = async () => {
    try {
      const response = await axios.get(`${API}/marketplace/listings`);
      // Fetch ticket details for each listing
      const listingsWithDetails = await Promise.all(
        response.data.map(async (listing) => {
          try {
            const ticketRes = await axios.get(`${API}/tickets/${listing.ticket_id}`);
            const eventRes = await axios.get(`${API}/events/${ticketRes.data.event_id}`);
            return { ...listing, ticket: ticketRes.data, event: eventRes.data };
          } catch (error) {
            return listing;
          }
        })
      );
      setListings(listingsWithDetails);
    } catch (error) {
      console.error("Error fetching listings:", error);
      toast.error("Failed to load marketplace");
    } finally {
      setLoading(false);
    }
  };

  const handleBuyListing = async (listing) => {
    if (!wallet) {
      toast.error("Please connect your wallet first");
      return;
    }

    try {
      await axios.post(`${API}/marketplace/buy`, {
        resale_id: listing.resale_id,
        buyer_address: wallet.address
      });
      toast.success("Ticket purchased from marketplace!");
      await refreshWallet();
      fetchListings();
    } catch (error) {
      console.error("Error buying listing:", error);
      toast.error(error.response?.data?.detail || "Failed to purchase ticket");
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading marketplace...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Marketplace</h1>
        <p className="text-muted-foreground">Buy resale tickets from other users</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {listings.map((listing) => (
          <Card key={listing.resale_id} className="overflow-hidden hover:shadow-lg transition-shadow" data-testid={`listing-card-${listing.resale_id}`}>
            <div className="h-48 bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center">
              <Ticket className="h-20 w-20 text-blue-400" />
            </div>
            <CardHeader>
              <div className="flex items-center justify-between mb-2">
                <Badge data-testid={`listing-status-${listing.resale_id}`}>Resale</Badge>
                <span className="text-lg font-bold" data-testid={`listing-price-${listing.resale_id}`}>{listing.listing_price} ETH</span>
              </div>
              <CardTitle data-testid={`listing-event-${listing.resale_id}`}>{listing.event?.name || "Event"}</CardTitle>
              <CardDescription>
                <div className="text-sm space-y-1">
                  <div>Original: {listing.original_price} ETH</div>
                  <div>Markup: {listing.markup_percentage?.toFixed(2)}%</div>
                </div>
              </CardDescription>
            </CardHeader>
            <CardFooter>
              <Button
                className="w-full"
                onClick={() => handleBuyListing(listing)}
                data-testid={`buy-listing-btn-${listing.resale_id}`}
              >
                <ShoppingCart className="mr-2 h-4 w-4" />
                Buy Now
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {listings.length === 0 && (
        <div className="text-center py-12">
          <ShoppingCart className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No listings available</h3>
          <p className="text-muted-foreground">Check back later for resale tickets</p>
        </div>
      )}
    </div>
  );
};

// My Tickets Page
const MyTicketsPage = ({ wallet, refreshWallet }) => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showListDialog, setShowListDialog] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [listPrice, setListPrice] = useState("");

  useEffect(() => {
    if (wallet) {
      fetchTickets();
    }
  }, [wallet]);

  const fetchTickets = async () => {
    try {
      const response = await axios.get(`${API}/tickets/wallet/${wallet.address}`);
      // Fetch event details for each ticket
      const ticketsWithEvents = await Promise.all(
        response.data.map(async (ticket) => {
          try {
            const eventRes = await axios.get(`${API}/events/${ticket.event_id}`);
            return { ...ticket, event: eventRes.data };
          } catch (error) {
            return ticket;
          }
        })
      );
      setTickets(ticketsWithEvents);
    } catch (error) {
      console.error("Error fetching tickets:", error);
      toast.error("Failed to load tickets");
    } finally {
      setLoading(false);
    }
  };

  const handleListTicket = (ticket) => {
    setSelectedTicket(ticket);
    setListPrice(ticket.event?.base_price?.toString() || "");
    setShowListDialog(true);
  };

  const confirmListTicket = async () => {
    if (!listPrice || parseFloat(listPrice) <= 0) {
      toast.error("Please enter a valid price");
      return;
    }

    try {
      await axios.post(`${API}/marketplace/list`, {
        ticket_id: selectedTicket.ticket_id,
        seller_address: wallet.address,
        listing_price: parseFloat(listPrice)
      });
      toast.success("Ticket listed on marketplace!");
      setShowListDialog(false);
      fetchTickets();
    } catch (error) {
      console.error("Error listing ticket:", error);
      toast.error(error.response?.data?.detail || "Failed to list ticket");
    }
  };

  if (!wallet) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <WalletIcon className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
        <h3 className="text-lg font-medium mb-2">Connect your wallet</h3>
        <p className="text-muted-foreground">Please connect your wallet to view your tickets</p>
      </div>
    );
  }

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading tickets...</div>;
  }

  return (
    <>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">My Tickets</h1>
          <p className="text-muted-foreground">View and manage your NFT tickets</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tickets.map((ticket) => (
            <Card key={ticket.token_id} className="overflow-hidden" data-testid={`ticket-card-${ticket.token_id}`}>
              <div className="h-48 bg-gradient-to-br from-purple-100 to-purple-200 flex items-center justify-center">
                <Ticket className="h-20 w-20 text-purple-400" />
              </div>
              <CardHeader>
                <div className="flex items-center justify-between mb-2">
                  <Badge variant={ticket.status === 'MINTED' ? 'default' : ticket.status === 'LISTED' ? 'secondary' : 'outline'} data-testid={`ticket-status-${ticket.token_id}`}>
                    {ticket.status}
                  </Badge>
                </div>
                <CardTitle data-testid={`ticket-event-${ticket.token_id}`}>{ticket.event?.name || "Event"}</CardTitle>
                <CardDescription>
                  <div className="text-sm space-y-1">
                    <div>Token ID: {ticket.token_id.slice(0, 8)}...</div>
                    <div>Minted: {new Date(ticket.minted_at).toLocaleDateString()}</div>
                  </div>
                </CardDescription>
              </CardHeader>
              <CardFooter>
                {ticket.status === 'MINTED' && (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handleListTicket(ticket)}
                    data-testid={`list-ticket-btn-${ticket.token_id}`}
                  >
                    List for Sale
                  </Button>
                )}
                {ticket.status === 'LISTED' && (
                  <Badge variant="secondary" className="w-full justify-center">Listed on Marketplace</Badge>
                )}
                {ticket.status === 'USED' && (
                  <Badge variant="outline" className="w-full justify-center">Ticket Used</Badge>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>

        {tickets.length === 0 && (
          <div className="text-center py-12">
            <Ticket className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No tickets yet</h3>
            <p className="text-muted-foreground">Purchase tickets from available events</p>
          </div>
        )}
      </div>

      <Dialog open={showListDialog} onOpenChange={setShowListDialog}>
        <DialogContent data-testid="list-ticket-dialog">
          <DialogHeader>
            <DialogTitle>List Ticket for Sale</DialogTitle>
            <DialogDescription>
              Set your resale price for this ticket
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="list-price">Price (ETH)</Label>
              <Input
                id="list-price"
                type="number"
                step="0.01"
                placeholder="0.00"
                value={listPrice}
                onChange={(e) => setListPrice(e.target.value)}
                data-testid="list-price-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={confirmListTicket} data-testid="confirm-list-btn">List Ticket</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

// Create Event Page
const CreateEventPage = ({ wallet }) => {
  const [formData, setFormData] = useState({
    name: "",
    venue_id: "",
    event_date: "",
    start_time: "19:00:00",
    end_time: "23:00:00",
    total_supply: "",
    base_price: ""
  });
  const [venues, setVenues] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchVenues();
  }, []);

  const fetchVenues = async () => {
    try {
      const response = await axios.get(`${API}/venues`);
      setVenues(response.data);

      // Create default venue if none exist
      if (response.data.length === 0) {
        const newVenue = await axios.post(`${API}/venues`, {
          name: "Default Arena",
          location: "City Center",
          capacity: 5000
        });
        setVenues([newVenue.data]);
        setFormData(prev => ({ ...prev, venue_id: newVenue.data.venue_id }));
      } else {
        setFormData(prev => ({ ...prev, venue_id: response.data[0].venue_id }));
      }
    } catch (error) {
      console.error("Error fetching venues:", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await axios.post(`${API}/events`, {
        venue_id: parseInt(formData.venue_id),
        name: formData.name,
        event_date: formData.event_date,
        start_time: formData.start_time,
        end_time: formData.end_time,
        total_supply: parseInt(formData.total_supply),
        base_price: parseFloat(formData.base_price)
      });
      toast.success("Event created successfully!");
      navigate("/");
    } catch (error) {
      console.error("Error creating event:", error);
      toast.error(error.response?.data?.detail || "Failed to create event");
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Create Event</h1>
        <p className="text-muted-foreground">Set up a new event and mint NFT tickets</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>Event Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Event Name</Label>
              <Input
                id="name"
                name="name"
                placeholder="Bitcoin Conference 2025"
                value={formData.name}
                onChange={handleChange}
                required
                data-testid="event-name-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="venue_id">Venue</Label>
              <select
                id="venue_id"
                name="venue_id"
                value={formData.venue_id}
                onChange={handleChange}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                required
                data-testid="venue-select"
              >
                {venues.map((venue) => (
                  <option key={venue.venue_id} value={venue.venue_id}>
                    {venue.name} - {venue.location}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="event_date">Event Date</Label>
              <Input
                id="event_date"
                name="event_date"
                type="datetime-local"
                value={formData.event_date}
                onChange={handleChange}
                required
                data-testid="event-date-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="total_supply">Total Tickets</Label>
                <Input
                  id="total_supply"
                  name="total_supply"
                  type="number"
                  placeholder="100"
                  value={formData.total_supply}
                  onChange={handleChange}
                  required
                  data-testid="total-supply-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="base_price">Price (ETH)</Label>
                <Input
                  id="base_price"
                  name="base_price"
                  type="number"
                  step="0.01"
                  placeholder="0.05"
                  value={formData.base_price}
                  onChange={handleChange}
                  required
                  data-testid="event-price-input"
                />
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" data-testid="create-event-btn">
              <Plus className="mr-2 h-4 w-4" />
              Create Event
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

function App() {
  return (
    <WalletContext>
      {({ wallet, connectWallet, disconnectWallet, refreshWallet, loading }) => (
        <div className="App min-h-screen bg-slate-50">
          <Toaster position="top-right" />
          <BrowserRouter>
            <Header wallet={wallet} onConnect={connectWallet} onDisconnect={disconnectWallet} />
            <Routes>
              <Route path="/" element={<EventsPage wallet={wallet} refreshWallet={refreshWallet} />} />
              <Route path="/marketplace" element={<MarketplacePage wallet={wallet} refreshWallet={refreshWallet} />} />
              <Route path="/my-tickets" element={<MyTicketsPage wallet={wallet} refreshWallet={refreshWallet} />} />
              <Route path="/create-event" element={<CreateEventPage wallet={wallet} />} />
            </Routes>
          </BrowserRouter>
        </div>
      )}
    </WalletContext>
  );
}

export default App;
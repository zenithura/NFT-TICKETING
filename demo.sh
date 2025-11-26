#!/bin/bash

echo "================================================"
echo "NFT Ticketing Platform - Complete Demo"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Checking Hardhat Node${NC}"
echo "Hardhat node should be running on http://127.0.0.1:8545"
curl -s -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' http://127.0.0.1:8545 | jq .
echo ""

echo -e "${BLUE}Step 2: Checking Backend Server${NC}"
echo "Backend server should be running on http://localhost:8000"
curl -s http://localhost:8000/api/ | jq .
echo ""

echo -e "${BLUE}Step 3: Creating Test Wallet${NC}"
WALLET_ADDRESS="0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
echo "Using Hardhat test account: $WALLET_ADDRESS"
WALLET_RESPONSE=$(curl -s -X POST http://localhost:8000/api/wallet/connect \
  -H "Content-Type: application/json" \
  -d "{\"address\": \"$WALLET_ADDRESS\"}")
echo "$WALLET_RESPONSE" | jq .
WALLET_ID=$(echo "$WALLET_RESPONSE" | jq -r '.wallet_id')
echo -e "${GREEN}✓ Wallet created with ID: $WALLET_ID${NC}"
echo ""

echo -e "${BLUE}Step 4: Creating Test Venue${NC}"
VENUE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/venues \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Crypto Arena",
    "location": "123 Blockchain Street",
    "city": "Web3 City",
    "country": "Decentraland",
    "capacity": 1000
  }')
echo "$VENUE_RESPONSE" | jq .
VENUE_ID=$(echo "$VENUE_RESPONSE" | jq -r '.venue_id')
echo -e "${GREEN}✓ Venue created with ID: $VENUE_ID${NC}"
echo ""

echo -e "${BLUE}Step 5: Creating Test Event${NC}"
EVENT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d "{
    \"venue_id\": $VENUE_ID,
    \"name\": \"NFT Conference 2025\",
    \"description\": \"The biggest NFT event of the year\",
    \"event_date\": \"2025-12-31\",
    \"start_time\": \"18:00:00\",
    \"end_time\": \"23:00:00\",
    \"total_supply\": 100,
    \"base_price\": 0.1
  }")
echo "$EVENT_RESPONSE" | jq .
EVENT_ID=$(echo "$EVENT_RESPONSE" | jq -r '.event_id')
echo -e "${GREEN}✓ Event created with ID: $EVENT_ID${NC}"
echo ""

echo -e "${YELLOW}Step 6: Minting NFT Ticket (This will interact with the blockchain!)${NC}"
echo "This may take a few seconds..."
MINT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/tickets/mint \
  -H "Content-Type: application/json" \
  -d "{
    \"event_id\": $EVENT_ID,
    \"buyer_address\": \"$WALLET_ADDRESS\"
  }")
echo "$MINT_RESPONSE" | jq .
TICKET_ID=$(echo "$MINT_RESPONSE" | jq -r '.ticket_id')
TX_HASH=$(echo "$MINT_RESPONSE" | jq -r '.transaction_hash // empty')

if [ -n "$TX_HASH" ] && [ "$TX_HASH" != "null" ]; then
  echo -e "${GREEN}✓ Ticket minted successfully!${NC}"
  echo -e "${GREEN}  Ticket ID: $TICKET_ID${NC}"
  echo -e "${GREEN}  Transaction Hash: $TX_HASH${NC}"
else
  echo -e "${YELLOW}⚠ Ticket created in database, but blockchain minting may have failed${NC}"
  echo -e "${YELLOW}  Ticket ID: $TICKET_ID${NC}"
fi
echo ""

echo -e "${BLUE}Step 7: Retrieving User's Tickets${NC}"
TICKETS_RESPONSE=$(curl -s http://localhost:8000/api/tickets/wallet/$WALLET_ADDRESS)
echo "$TICKETS_RESPONSE" | jq .
TICKET_COUNT=$(echo "$TICKETS_RESPONSE" | jq '. | length')
echo -e "${GREEN}✓ User has $TICKET_COUNT ticket(s)${NC}"
echo ""

echo -e "${BLUE}Step 8: Getting Event Details${NC}"
EVENT_DETAILS=$(curl -s http://localhost:8000/api/events/$EVENT_ID)
echo "$EVENT_DETAILS" | jq .
AVAILABLE=$(echo "$EVENT_DETAILS" | jq -r '.available_tickets')
echo -e "${GREEN}✓ Event has $AVAILABLE tickets remaining${NC}"
echo ""

echo "================================================"
echo -e "${GREEN}Demo Complete!${NC}"
echo "================================================"
echo ""
echo "Summary:"
echo "- Wallet Address: $WALLET_ADDRESS"
echo "- Venue ID: $VENUE_ID"
echo "- Event ID: $EVENT_ID"
echo "- Ticket ID: $TICKET_ID"
if [ -n "$TX_HASH" ] && [ "$TX_HASH" != "null" ]; then
  echo "- Blockchain TX: $TX_HASH"
fi
echo ""
echo "Next steps:"
echo "1. Check the Hardhat node console for transaction logs"
echo "2. View API docs at http://localhost:8000/docs"
echo "3. Try the frontend integration with MetaMask"
echo ""

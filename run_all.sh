#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================"
echo "NFT Ticketing Platform - Full Stack Launch"
echo "================================================"
echo -e "${NC}"

# Kill any existing processes on ports
echo -e "${BLUE}[*] Cleaning up existing processes...${NC}"
fuser -k 8545/tcp 2>/dev/null
fuser -k 8000/tcp 2>/dev/null
fuser -k 5173/tcp 2>/dev/null
# Don't kill Docker ports (5001, 8050, 5432, 6379) as we manage them with docker-compose

# 1. Start Hardhat Node
echo -e "${BLUE}[1/5] Starting Local Blockchain (Hardhat)...${NC}"
cd smart-contracts
npm install > /dev/null 2>&1
npx hardhat node > ../hardhat.log 2>&1 &
HARDHAT_PID=$!
echo -e "${GREEN}✓ Blockchain running (PID: $HARDHAT_PID)${NC}"
sleep 5 # Wait for node to start

# 2. Deploy Smart Contracts
echo -e "${BLUE}[2/5] Deploying Smart Contracts...${NC}"
npx hardhat run scripts/deploy.js --network localhost > ../deploy.log 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Contracts deployed${NC}"
else
    echo -e "${RED}✗ Contract deployment failed. Check deploy.log${NC}"
fi
cd ..

# 3. Start Sprint 3 Services (Docker)
echo -e "${BLUE}[3/5] Starting Sprint 3 Services (Fraud API, Dashboard, DB)...${NC}"
cd sprint3
# Check if docker-compose exists, else use docker compose
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi
echo -e "${GREEN}✓ Docker services started${NC}"
cd ..

# 4. Start Backend
echo -e "${BLUE}[4/5] Starting Python Backend...${NC}"
cd frontend_with_backend/backend
if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python server.py > ../../backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend running (PID: $BACKEND_PID)${NC}"
cd ../..

# 5. Start Frontend
echo -e "${BLUE}[5/5] Starting Frontend...${NC}"
cd frontend
npm install > /dev/null 2>&1
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend running (PID: $FRONTEND_PID)${NC}"
cd ..

echo -e "${BLUE}================================================"
echo "All services are running!"
echo "================================================"
echo -e "${GREEN}Blockchain: http://127.0.0.1:8545${NC}"
echo -e "${GREEN}Backend:    http://localhost:8000${NC}"
echo -e "${GREEN}Frontend:   http://localhost:5173${NC}"
echo -e "${GREEN}Fraud API:  http://localhost:5001${NC}"
echo -e "${GREEN}Dashboard:  http://localhost:8050${NC}"
echo ""
echo -e "${YELLOW}Logs are being written to:${NC}"
echo "- hardhat.log"
echo "- deploy.log"
echo "- backend.log"
echo "- frontend.log"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait for user to exit
trap "kill $HARDHAT_PID $BACKEND_PID $FRONTEND_PID; exit" SIGINT
wait

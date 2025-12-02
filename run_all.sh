#!/bin/bash
# File header: Full-stack launch script that starts all platform services.
# Orchestrates blockchain node, smart contract deployment, backend API, frontend, and Sprint 3 services.

# Purpose: ANSI color codes for terminal output formatting.
# Side effects: None - constants only.
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================"
echo "NFT Ticketing Platform - Full Stack Launch"
echo "================================================"
echo -e "${NC}"

# Purpose: Terminate any existing processes using required ports to avoid conflicts.
# Side effects: Kills processes on ports 8545, 8000, 5173.
echo -e "${BLUE}[*] Cleaning up existing processes...${NC}"
fuser -k 8545/tcp 2>/dev/null
fuser -k 8000/tcp 2>/dev/null
fuser -k 5173/tcp 2>/dev/null
# Don't kill Docker ports (5001, 8050, 5432, 6379) as we manage them with docker-compose

# Purpose: Start local Hardhat blockchain node for development and testing.
# Side effects: Installs npm dependencies, starts blockchain node in background, writes logs.
echo -e "${BLUE}[1/5] Starting Local Blockchain (Hardhat)...${NC}"
cd smart-contracts
npm install > /dev/null 2>&1
npx hardhat node > ../hardhat.log 2>&1 &
HARDHAT_PID=$!
echo -e "${GREEN}✓ Blockchain running (PID: $HARDHAT_PID)${NC}"
sleep 5 # Wait for node to start

# Purpose: Deploy TicketManager smart contract to the local blockchain.
# Side effects: Executes deployment script, writes transaction logs to file.
echo -e "${BLUE}[2/5] Deploying Smart Contracts...${NC}"
npx hardhat run scripts/deploy.js --network localhost > ../deploy.log 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Contracts deployed${NC}"
else
    echo -e "${RED}✗ Contract deployment failed. Check deploy.log${NC}"
fi
cd ..

# Purpose: Start Sprint 3 services (fraud detection API, monitoring dashboard, databases) via Docker.
# Side effects: Starts Docker containers in detached mode, initializes databases.
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

# Purpose: Start FastAPI backend server with Python virtual environment.
# Side effects: Creates venv if missing, installs dependencies, starts server in background.
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

# Purpose: Start frontend development server with Vite.
# Side effects: Installs npm dependencies, starts dev server in background, writes logs.
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

# Purpose: Set up signal handler to gracefully terminate all background processes on Ctrl+C.
# Side effects: Registers trap handler, waits for user interrupt.
trap "kill $HARDHAT_PID $BACKEND_PID $FRONTEND_PID; exit" SIGINT
wait

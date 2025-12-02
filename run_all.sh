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
fuser -k 3000/tcp 2>/dev/null
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
    # Extract contract address
    CONTRACT_ADDRESS=$(grep "TicketManager deployed to:" ../deploy.log | awk '{print $4}')
    echo -e "${GREEN}  Address: $CONTRACT_ADDRESS${NC}"
    export SMART_CONTRACT_ADDRESS=$CONTRACT_ADDRESS
    export SERVER_WALLET_PRIVATE_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    export SERVER_WALLET_ADDRESS="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
else
    echo -e "${RED}✗ Contract deployment failed. Check deploy.log${NC}"
fi
cd ..

# 3. Start Sprint 3 Services (Docker)
echo -e "${BLUE}[3/5] Starting Sprint 3 Services (Fraud API, Dashboard, DB)...${NC}"
cd sprint3
# Check if docker-compose exists, else use docker compose, else fallback to manual docker run
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ docker-compose failed.${NC}"
        exit 1
    fi
elif docker compose version &> /dev/null; then
    docker compose up -d
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ docker compose failed.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}[!] docker-compose not found. Falling back to manual docker run...${NC}"
    
    # Cleanup existing containers
    echo "Cleaning up old containers..."
    docker rm -f sprint3-postgres sprint3-redis sprint3-fraud-api sprint3-dashboard 2>/dev/null || true

    # Create network
    docker network create ticketing-net 2>/dev/null || true

    # Postgres
    echo "Starting Postgres..."
    docker run -d --name sprint3-postgres --network ticketing-net \
        -e POSTGRES_DB=ticketing -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=${DB_PASSWORD:-change_me_in_prod} \
        -v postgres_data:/var/lib/postgresql/data -v $(pwd)/sql:/docker-entrypoint-initdb.d \
        -p 5432:5432 postgres:15

    # Redis
    echo "Starting Redis..."
    docker run -d --name sprint3-redis --network ticketing-net \
        -p 6379:6379 redis:7-alpine

    # Wait for DB and Redis
    echo "Waiting for DB and Redis to be ready..."
    sleep 10

    # Fraud API
    echo "Building and Starting Fraud API..."
    docker build -t sprint3-fraud-api -f Dockerfile.fraud_api .
    docker run -d --name sprint3-fraud-api --network ticketing-net \
        -e DB_HOST=sprint3-postgres -e DB_PORT=5432 -e DB_NAME=ticketing \
        -e DB_USER=admin -e DB_PASSWORD=${DB_PASSWORD:-change_me_in_prod} \
        -e REDIS_HOST=sprint3-redis -e REDIS_PORT=6379 \
        -v $(pwd)/ml_pipeline:/app/ml_pipeline -v $(pwd)/api:/app/api -v $(pwd)/demos/data:/app/demos/data \
        -p 5001:5001 sprint3-fraud-api

    # Dashboard
    echo "Building and Starting Dashboard..."
    docker build -t sprint3-dashboard -f Dockerfile.dashboard .
    docker run -d --name sprint3-dashboard --network ticketing-net \
        -e DB_HOST=sprint3-postgres -e REDIS_HOST=sprint3-redis \
        -v $(pwd)/monitoring:/app/monitoring -v $(pwd)/demos/data:/app/demos/data \
        -p 8050:8050 sprint3-dashboard
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
# Pass env vars
export SMART_CONTRACT_ADDRESS=$SMART_CONTRACT_ADDRESS
export SERVER_WALLET_PRIVATE_KEY=$SERVER_WALLET_PRIVATE_KEY
export SERVER_WALLET_ADDRESS=$SERVER_WALLET_ADDRESS
python -m uvicorn server:app --host 0.0.0.0 --port 8000 > ../../backend.log 2>&1 &
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
echo -e "${GREEN}Frontend:   http://localhost:3000${NC}"
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

#!/bin/bash

# Function to kill all background processes on exit
cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

echo "Starting NFT Ticketing Platform..."

# 1. Start Hardhat Node
echo "Starting Hardhat Node..."
cd smart_contracts
npx hardhat node > ../logs/hardhat.log 2>&1 &
HARDHAT_PID=$!
cd ..

# Wait for Hardhat Node to be ready
echo "Waiting for Hardhat Node..."
sleep 5

# 2. Deploy Contracts
echo "Deploying Contracts..."
cd smart_contracts
HARDHAT_TELEMETRY_DISABLED=1 npx hardhat run scripts/deploy.ts --network localhost
cd ..

# 3. Start Sprint 3 Services (Docker)
if [ -d "sprint3" ]; then
    echo "Starting Sprint 3 Services..."
    if docker compose version >/dev/null 2>&1; then
        cd sprint3
        docker compose up -d
        cd ..
    elif docker-compose version >/dev/null 2>&1; then
        cd sprint3
        docker-compose up -d
        cd ..
    else
        echo "WARNING: Docker Compose not found. Skipping Sprint 3 services."
    fi
else
    echo "Sprint 3 directory not found. Skipping Docker services."
fi

# 3b. Start Monitoring Dashboard
echo "Starting Monitoring Dashboard..."
# Check if venv exists, otherwise assume python3 is available
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
fi
python backend/monitoring/dashboard.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!

# 4. Start Backend
echo "Starting Backend..."
cd backend
# Check if venv exists, otherwise assume python3 is available
if [ -d "venv" ]; then
    source venv/bin/activate
fi
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 5. Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "All services started!"
echo "Frontend: http://localhost:5173 (or similar)"
echo "Backend: http://localhost:8000"
echo "Hardhat Node: http://localhost:8545"
echo "Press Ctrl+C to stop all services."

# Wait for any process to exit
wait $HARDHAT_PID $BACKEND_PID $FRONTEND_PID $DASHBOARD_PID

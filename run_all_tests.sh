#!/bin/bash
# Full-stack test runner script

set -e

echo "🧪 Running Full-Stack Automated Tests"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if services are running
check_service() {
    local url=$1
    local name=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $name is not running"
        return 1
    fi
}

echo ""
echo "1️⃣  Checking services..."
check_service "http://localhost:8000/health" "Backend API"
check_service "http://localhost:5173" "Frontend Dev Server"

echo ""
echo "2️⃣  Running Backend Tests..."
cd backend

if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠${NC} Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

echo "Running pytest..."
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

BACKEND_TEST_EXIT=$?

cd ..

echo ""
echo "3️⃣  Running Frontend Tests..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠${NC} node_modules not found. Installing..."
    npm install
fi

echo "Running Cypress tests..."
npm run e2e:headless

FRONTEND_TEST_EXIT=$?

cd ..

echo ""
echo "======================================"
if [ $BACKEND_TEST_EXIT -eq 0 ] && [ $FRONTEND_TEST_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi


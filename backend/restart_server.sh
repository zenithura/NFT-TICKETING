#!/bin/bash
# Script to restart the backend server

set -e

echo "Stopping existing server processes..."
pkill -f "python.*main.py" || echo "No existing processes found"

sleep 2

echo "Checking if port 8000 is free..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Port 8000 is still in use. Killing processes..."
    kill -9 $(lsof -ti:8000) 2>/dev/null || true
    sleep 1
fi

echo "Starting server..."
cd "$(dirname "$0")"
source venv/bin/activate
python main.py


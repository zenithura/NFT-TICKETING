#!/bin/bash

echo "🚀 Starting NFT Ticketing Backend Server..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from .env.new or .env.example"
    echo ""
    echo "Steps:"
    echo "1. Copy .env.new to .env"
    echo "2. Add your Supabase service_role key"
    echo "3. Run this script again"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt --quiet

# Start the server
echo ""
echo "✅ Starting server at http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn server:app --reload --host 0.0.0.0 --port 8000

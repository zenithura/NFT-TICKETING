#!/bin/bash
# File header: Backend server startup script that sets up Python environment and starts FastAPI server.
# Validates configuration, creates virtual environment if needed, and launches uvicorn server.

echo "🚀 Starting NFT Ticketing Backend Server..."
echo ""

# Purpose: Validate that .env configuration file exists before starting server.
# Side effects: Exits script with error message if .env file is missing.
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

# Purpose: Create Python virtual environment if it doesn't exist.
# Side effects: Creates venv directory and Python virtual environment.
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Purpose: Activate Python virtual environment for dependency isolation.
# Side effects: Modifies shell environment to use venv Python and packages.
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Purpose: Install or upgrade Python dependencies from requirements.txt.
# Side effects: Installs packages via pip, may download from PyPI.
echo "📚 Installing dependencies..."
pip install -r requirements.txt --quiet

# Purpose: Start FastAPI server using uvicorn ASGI server.
# Side effects: Starts HTTP server on port 8000, binds to all interfaces.
echo ""
echo "✅ Starting server at http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Purpose: Run uvicorn without auto-reload to avoid file watch limit issues.
# Side effects: Starts server process, serves FastAPI application.
# Note: To enable auto-reload, first increase system limit: sudo sysctl fs.inotify.max_user_watches=524288
uvicorn server:app --host 0.0.0.0 --port 8000

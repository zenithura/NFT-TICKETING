
#!/bin/bash
# Backend startup script for NFT Ticketing Platform

set -e

echo "=========================================="
echo "NFT Ticketing Platform - Backend Setup"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python version
echo "1️⃣  Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.8+"; exit 1; }

# Create virtual environment if it doesn't exist
echo ""
echo "2️⃣  Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "3️⃣  Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo ""
echo "4️⃣  Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Check for .env file
echo ""
echo "5️⃣  Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env file template..."
    cat > .env << EOF
# Supabase Configuration
SUPABASE_URL=your-supabase-url-here
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# JWT Configuration
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
EOF
    echo "✅ .env file created with template"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add your Supabase credentials!"
    echo "   - SUPABASE_URL: Your Supabase project URL"
    echo "   - SUPABASE_KEY: Your Supabase anon/public key"
    echo "   - SUPABASE_SERVICE_KEY: Your Supabase service role key"
    echo ""
    read -p "Press Enter after you've updated .env file..."
else
    echo "✅ .env file found"
fi

# Check if required environment variables are set
echo ""
echo "6️⃣  Validating environment variables..."
source .env
if [ -z "$SUPABASE_URL" ] || [ "$SUPABASE_URL" = "your-supabase-url-here" ]; then
    echo "❌ SUPABASE_URL not configured in .env"
    exit 1
fi
if [ -z "$SUPABASE_SERVICE_KEY" ] || [ "$SUPABASE_SERVICE_KEY" = "your-service-role-key-here" ]; then
    echo "❌ SUPABASE_SERVICE_KEY not configured in .env"
    exit 1
fi
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "❌ JWT_SECRET_KEY not configured in .env"
    exit 1
fi
echo "✅ Environment variables validated"

# Start the server
echo ""
echo "=========================================="
echo "🚀 Starting Backend Server..."
echo "=========================================="
echo ""
echo "Server will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python main.py


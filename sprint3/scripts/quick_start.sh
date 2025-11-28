#!/bin/bash
# Quick Start Script for Sprint 3 Demo

set -e

echo "=========================================="
echo "Sprint 3 - Quick Start Setup"
echo "=========================================="
echo ""

# Check Python version
echo "1️⃣  Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Create virtual environment
echo ""
echo "2️⃣  Creating virtual environment..."
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

# Install dependencies
echo ""
echo "4️⃣  Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# Generate sample data
echo ""
echo "5️⃣  Generating sample transaction data..."
python demos/generate_sample_data.py
echo "✅ Sample data generated"

# Train ML model
echo ""
echo "6️⃣  Training fraud detection model..."
python ml_pipeline/train_fraud_model.py
echo "✅ Model trained"

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "🚀 You can now run:"
echo ""
echo "  1. Fraud Detection API:"
echo "     python api/fraud_api.py"
echo "     Then visit: http://localhost:5001/health"
echo ""
echo "  2. Monitoring Dashboard:"
echo "     python monitoring/dashboard.py"
echo "     Then visit: http://localhost:8050"
echo ""
echo "  3. Test API:"
echo "     curl -X POST http://localhost:5001/api/v1/ml/predict/fraud \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"transaction_id\": \"test_001\", \"wallet_address\": \"0x123\", \"ticket_id\": \"evt_001\", \"price_paid\": 50.00}'"
echo ""
echo "=========================================="

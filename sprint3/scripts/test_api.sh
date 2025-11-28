#!/bin/bash
# Test the fraud detection API

echo "=========================================="
echo "Testing Fraud Detection API"
echo "=========================================="
echo ""

API_URL="http://localhost:5001"

# Test 1: Health check
echo "1️⃣  Testing health endpoint..."
curl -s $API_URL/health | python3 -m json.tool
echo ""

# Test 2: Single prediction (low risk)
echo ""
echo "2️⃣  Testing single prediction (low risk transaction)..."
curl -s -X POST $API_URL/api/v1/ml/predict/fraud \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test_001",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "ticket_id": "evt_001",
    "price_paid": 50.00,
    "floor_price": 50.00
  }' | python3 -m json.tool
echo ""

# Test 3: Single prediction (high risk)
echo ""
echo "3️⃣  Testing single prediction (high risk transaction)..."
curl -s -X POST $API_URL/api/v1/ml/predict/fraud \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test_002",
    "wallet_address": "0xSUSPICIOUS",
    "ticket_id": "evt_002",
    "price_paid": 500.00,
    "floor_price": 100.00,
    "txn_velocity_1h": 15,
    "wallet_age_days": 0.5,
    "geo_velocity_flag": true
  }' | python3 -m json.tool
echo ""

# Test 4: Batch prediction
echo ""
echo "4️⃣  Testing batch prediction..."
curl -s -X POST $API_URL/api/v1/ml/batch/predict \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {
        "transaction_id": "batch_001",
        "wallet_address": "0x123",
        "ticket_id": "evt_001",
        "price_paid": 50.00
      },
      {
        "transaction_id": "batch_002",
        "wallet_address": "0x456",
        "ticket_id": "evt_002",
        "price_paid": 300.00,
        "floor_price": 100.00
      }
    ]
  }' | python3 -m json.tool
echo ""

# Test 5: Model info
echo ""
echo "5️⃣  Getting model information..."
curl -s $API_URL/api/v1/ml/model/info | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ API tests complete!"
echo "=========================================="

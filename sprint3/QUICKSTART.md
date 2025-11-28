# 🚀 Sprint 3 - Quick Start Guide

## One-Command Setup

Run everything with a single command:

```bash
cd /home/mahammad/NFT-TICKETING/sprint3
./scripts/quick_start.sh
```

This will:
1. ✅ Create Python virtual environment
2. ✅ Install all dependencies
3. ✅ Generate 10,000 sample transactions
4. ✅ Train XGBoost fraud detection model
5. ✅ Prepare all components for demo

---

## Running the Components

### Option 1: Fraud Detection API

```bash
# Terminal 1: Start the API
cd /home/mahammad/NFT-TICKETING/sprint3
source venv/bin/activate
python api/fraud_api.py
```

Visit: **http://localhost:5001/health**

Test it:
```bash
# Terminal 2: Test the API
./scripts/test_api.sh
```

### Option 2: Monitoring Dashboard

```bash
# Terminal 1: Start the dashboard
cd /home/mahammad/NFT-TICKETING/sprint3
source venv/bin/activate
python monitoring/dashboard.py
```

Visit: **http://localhost:8050** in your browser

You'll see:
- 📊 Real-time KPIs (transactions, fraud rate, latency, revenue)
- 📈 Fraud score distribution chart
- 📉 Transaction volume over time
- 🚨 Recent high-risk transactions table
- Auto-refresh every 5 seconds

### Option 3: Both Together (Recommended)

```bash
# Terminal 1: API
cd /home/mahammad/NFT-TICKETING/sprint3
source venv/bin/activate
python api/fraud_api.py

# Terminal 2: Dashboard
cd /home/mahammad/NFT-TICKETING/sprint3
source venv/bin/activate
python monitoring/dashboard.py
```

Then open both:
- API: http://localhost:5001
- Dashboard: http://localhost:8050

---

## What You Can Do

### 1. Test Fraud Detection

```bash
# Low risk transaction (should be APPROVED)
curl -X POST http://localhost:5001/api/v1/ml/predict/fraud \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "demo_001",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "ticket_id": "evt_001",
    "price_paid": 50.00,
    "floor_price": 50.00
  }'

# High risk transaction (should be BLOCKED or REVIEW)
curl -X POST http://localhost:5001/api/v1/ml/predict/fraud \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "demo_002",
    "wallet_address": "0xNEW_SUSPICIOUS",
    "ticket_id": "evt_002",
    "price_paid": 500.00,
    "floor_price": 100.00,
    "txn_velocity_1h": 20,
    "wallet_age_days": 0.1,
    "geo_velocity_flag": true
  }'
```

### 2. View Live Dashboard

Open http://localhost:8050 and watch:
- KPIs update every 5 seconds
- Fraud score scatter plot
- Transaction volume trends
- Recent high-risk transactions

### 3. Explore the Data

```bash
# View generated sample data
head -20 demos/data/sample_transactions.csv

# Check model performance
cat ml_pipeline/models/model_metadata.json | python3 -m json.tool
```

---

## File Structure

```
sprint3/
├── api/
│   └── fraud_api.py              ← Fraud detection API
├── monitoring/
│   └── dashboard.py              ← Interactive dashboard
├── ml_pipeline/
│   ├── train_fraud_model.py      ← Model training
│   └── models/
│       ├── fraud_model_v1.2.3.pkl
│       └── model_metadata.json
├── demos/
│   ├── generate_sample_data.py   ← Sample data generator
│   └── data/
│       ├── sample_transactions.csv
│       ├── train_data.csv
│       └── test_data.csv
├── scripts/
│   ├── quick_start.sh            ← Automated setup
│   └── test_api.sh               ← API testing
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

---

## Troubleshooting

### Model not found error

```bash
# Generate data and train model
python demos/generate_sample_data.py
python ml_pipeline/train_fraud_model.py
```

### Port already in use

```bash
# Kill existing process
lsof -ti:5001 | xargs kill -9  # For API
lsof -ti:8050 | xargs kill -9  # For dashboard
```

### Dependencies missing

```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## Next Steps

1. ✅ **Explore the dashboard** - See real-time fraud detection in action
2. ✅ **Test the API** - Send different transaction patterns
3. ✅ **Review the code** - Check implementation details
4. ✅ **Integrate** - Connect to your existing NFT ticketing backend

---

## Integration Example

Add to your existing backend (`frontend_with_backend/backend/routes/tickets.py`):

```python
import requests

FRAUD_API_URL = "http://localhost:5001/api/v1/ml/predict/fraud"

@app.route('/api/tickets/buy', methods=['POST'])
def buy_ticket():
    data = request.get_json()
    
    # Call fraud detection
    fraud_check = requests.post(FRAUD_API_URL, json={
        'transaction_id': data['transaction_id'],
        'wallet_address': data['wallet_address'],
        'ticket_id': data['ticket_id'],
        'price_paid': data['price_paid']
    })
    
    result = fraud_check.json()
    
    if result['decision'] == 'BLOCKED':
        return jsonify({'error': 'Transaction blocked'}), 403
    elif result['decision'] == 'MANUAL_REVIEW':
        return jsonify({'status': 'pending_review'}), 202
    
    # Proceed with purchase...
    return jsonify({'status': 'success'}), 200
```

---

**Need help?** Check the full documentation in the other markdown files!

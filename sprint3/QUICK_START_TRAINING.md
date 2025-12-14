# Quick Start: Training Models with Database

## Overview

This guide shows you how to connect your ML models to the database and train them.

## What Was Created

1. **`train_fraud_model_db.py`** - Trains fraud detection model using database data
2. **`train_mab_model.py`** - Initializes MAB pricing model with historical data
3. **Updated ETL Pipeline** - Now uses correct database schema (`orders`, `wallets`, `events`)
4. **Updated Feature Engineering** - Queries updated to match actual schema

## Quick Start

### 1. Configure Database Connection

Edit `sprint3/config/config.yaml` or set environment variables:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ticketing
export DB_USER=admin
export DB_PASSWORD=your_password
```

### 2. Train Fraud Detection Model

```bash
cd sprint3
python ml_pipeline/train_fraud_model_db.py
```

**What happens:**
- Connects to database
- Extracts transactions from last 90 days
- Engineers 10 features for each transaction
- Trains XGBoost model
- Saves model to `ml_pipeline/models/fraud_model_v1.2.3.pkl`

### 3. Train MAB Pricing Model

```bash
cd sprint3
python ml_pipeline/train_mab_model.py
```

**What happens:**
- Loads historical pricing data
- Infers pricing strategies used
- Calculates rewards for each strategy
- Initializes MAB with historical statistics
- Saves state to Redis

## Database Schema Requirements

The scripts expect these tables:
- `orders` - Transaction orders
- `wallets` - Wallet addresses
- `events` - Event information
- `tickets` - Ticket records
- `security_alerts` - Fraud labels (optional)
- `bot_detection` - Bot detection results (optional)

## How It Works

### Fraud Model Training Flow

```
Database → ETL Pipeline → Feature Engineering → Training → Model File
```

1. **Extract**: Query `orders` table for transactions
2. **Transform**: Join with `wallets` and `events` tables
3. **Feature Engineering**: Compute 10 ML features
4. **Label**: Use `security_alerts`/`bot_detection` or heuristics
5. **Train**: XGBoost classifier
6. **Save**: Model + metadata

### MAB Model Training Flow

```
Database → Historical Data → Strategy Inference → Reward Calculation → MAB Initialization → Redis
```

1. **Extract**: Query `orders` for pricing history
2. **Infer Strategies**: Determine which pricing strategy was used
3. **Calculate Rewards**: Revenue × conversion × popularity
4. **Initialize**: Update MAB arm statistics
5. **Save**: Store state in Redis

## Key Features

### Database Connection
- Uses connection pooling
- Handles errors gracefully
- Supports environment variables

### Feature Engineering
- 10 core features computed from database
- Caches results in Redis
- Handles missing data

### Model Training
- Handles class imbalance
- Cross-validation
- Comprehensive metrics
- Model versioning

## Troubleshooting

### "No data available"
- Check database has transactions: `SELECT COUNT(*) FROM orders;`
- Verify date range in script (default: 90 days)

### "Connection failed"
- Check `config.yaml` settings
- Test connection: `psql -h localhost -U admin -d ticketing`

### "No fraud labels"
- Script falls back to heuristic labels
- Add fraud labels to `security_alerts` table for better training

## Next Steps

1. Run training scripts
2. Check model files in `ml_pipeline/models/`
3. Update `config.yaml` with model paths
4. Test predictions using trained models

For detailed documentation, see `TRAINING_GUIDE.md`.


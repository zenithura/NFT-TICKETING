# Model Training Guide: Connecting Models to Database

This guide explains how to connect ML models to the database and train them using real transaction data.

## Overview

The NFT Ticketing platform has two main ML models:

1. **Fraud Detection Model** (XGBoost) - Binary classifier for detecting fraudulent transactions
2. **Multi-Armed Bandit (MAB) Pricing Model** - Reinforcement learning model for dynamic pricing

Both models can be trained using data from the PostgreSQL database.

## Architecture

```
┌─────────────────┐
│  PostgreSQL DB  │
│  (transactions, │
│   orders, etc.) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ETL Pipeline  │
│  (Extract,      │
│   Transform,    │
│   Load)         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature Engineer│
│  (10 core       │
│   features)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Training       │
│  Scripts        │
└─────────────────┘
```

## Database Connection Setup

### 1. Configuration

The database connection is configured in `sprint3/config/config.yaml`:

```yaml
database:
  host: ${DB_HOST:-localhost}
  port: ${DB_PORT:-5432}
  name: ${DB_NAME:-ticketing}
  user: ${DB_USER:-admin}
  password: ${DB_PASSWORD:-change_me_in_prod}
```

### 2. Environment Variables

Set these environment variables or update `config.yaml`:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ticketing
export DB_USER=admin
export DB_PASSWORD=your_password
```

### 3. Redis Connection (for MAB state)

```yaml
redis:
  host: ${REDIS_HOST:-localhost}
  port: ${REDIS_PORT:-6379}
  password: ${REDIS_PASSWORD:-}
  db: 0
```

## Training Fraud Detection Model

### Step 1: Prepare Database

Ensure your database has:
- `orders` table with completed transactions
- `security_alerts` table with fraud labels
- `bot_detection` table with bot detection results
- `wallets` table with wallet information
- `events` table with event data

### Step 2: Run Training Script

```bash
cd sprint3
python ml_pipeline/train_fraud_model_db.py
```

### What It Does

1. **Extracts Data**: Queries database for transactions from last 90 days
2. **Engineers Features**: Computes 10 core features for each transaction:
   - `txn_velocity_1h`: Transaction velocity in last hour
   - `wallet_age_days`: Age of wallet in days
   - `avg_ticket_hold_time`: Average time tickets are held
   - `event_popularity_score`: Event popularity metric
   - `price_deviation_ratio`: Deviation from base price
   - `cross_event_attendance`: Number of different events attended
   - `geo_velocity_flag`: Geographic velocity indicator
   - `payment_method_diversity`: Number of payment methods used
   - `social_graph_centrality`: Social network centrality
   - `time_to_first_resale`: Time until first resale

3. **Labels Data**: Uses fraud labels from `security_alerts` and `bot_detection` tables
4. **Trains Model**: Trains XGBoost classifier with class imbalance handling
5. **Evaluates**: Computes metrics (AUC-ROC, AUC-PR, F1, confusion matrix)
6. **Saves Model**: Saves to `sprint3/ml_pipeline/models/fraud_model_v1.2.3.pkl`

### Output

```
sprint3/ml_pipeline/models/
├── fraud_model_v1.2.3.pkl      # Trained model
└── model_metadata.json          # Training metadata
```

## Training MAB Pricing Model

### Step 1: Ensure Historical Data Exists

The MAB model needs historical transaction data to initialize. Ensure you have:
- `orders` table with pricing information
- `events` table with base prices
- `tickets` table with sales data

### Step 2: Run Training Script

```bash
cd sprint3
python ml_pipeline/train_mab_model.py
```

### What It Does

1. **Loads Historical Data**: Queries database for transactions from last 90 days
2. **Infers Pricing Strategies**: Determines which pricing strategy was used:
   - `baseline`: Fixed pricing
   - `surge_pricing`: Demand-based surge (>1.1x base)
   - `early_bird`: Early discount (<0.95x base)
   - `ml_pricing`: ML-predicted pricing (0.95x-1.1x base)

3. **Calculates Rewards**: Computes reward for each strategy:
   - Revenue: `price_paid`
   - Conversion: 1.0 if completed, 0.0 if failed
   - Popularity: `tickets_sold / capacity`
   - Combined: `revenue × conversion × popularity_factor`

4. **Initializes MAB**: Updates arm statistics with historical averages
5. **Simulates Online Learning**: Processes data in batches to simulate real-time learning
6. **Saves State**: Saves MAB state to Redis

### Output

MAB state is saved to Redis with keys:
- `mab:baseline`
- `mab:surge_pricing`
- `mab:early_bird`
- `mab:ml_pricing`

## Database Schema Requirements

### For Fraud Detection Training

```sql
-- Required tables:
orders (order_id, buyer_wallet_id, event_id, price, status, created_at)
wallets (wallet_id, address)
events (event_id, base_price, capacity, event_date)
security_alerts (alert_id, wallet_address, ...)
bot_detection (detection_id, wallet_address, ...)
tickets (ticket_id, event_id, owner_wallet_id, ...)
```

### For MAB Training

```sql
-- Required tables:
orders (order_id, event_id, price, status, created_at)
events (event_id, base_price, capacity, name)
tickets (ticket_id, event_id, ...)
```

## Feature Engineering

Features are computed by the `FeatureEngineer` class in `ml_pipeline/feature_engineering.py`.

### Real-time Features

For each transaction, features are computed on-the-fly:
- Queries database for wallet history
- Computes derived metrics
- Caches results in Redis (5-minute TTL)

### Batch Features

For training, features are computed in batch:
- Uses ETL pipeline to extract transactions
- Transforms data with derived features
- Engineers ML features for each transaction

## ETL Pipeline

The ETL pipeline (`data_control/etl_pipeline.py`) handles:

1. **Extract**: Queries database for transactions
2. **Transform**: Computes derived features
3. **Load**: Saves features to feature store table

### Running ETL Pipeline

```python
from data_control.etl_pipeline import get_etl_pipeline

etl = get_etl_pipeline()
etl.run_full_pipeline(since=datetime.now() - timedelta(days=30))
```

## Monitoring Training

### Check Training Progress

```bash
# View logs
tail -f logs/training.log

# Check model files
ls -lh sprint3/ml_pipeline/models/

# Check Redis state (for MAB)
redis-cli
> KEYS mab:*
> GET mab:baseline
```

### Validate Model

After training, validate the model:

```python
import pickle
import json

# Load model
with open('sprint3/ml_pipeline/models/fraud_model_v1.2.3.pkl', 'rb') as f:
    model = pickle.load(f)

# Load metadata
with open('sprint3/ml_pipeline/models/model_metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Model version: {metadata['model_version']}")
print(f"Training date: {metadata['training_date']}")
print(f"AUC-ROC: {metadata['metrics']['auc_roc']:.3f}")
```

## Troubleshooting

### Database Connection Issues

1. **Check connection settings**:
   ```python
   from data_control.db_connection import get_db_connection
   conn = get_db_connection()
   if conn is None:
       print("Connection failed - check config.yaml")
   ```

2. **Test connection**:
   ```bash
   psql -h localhost -U admin -d ticketing
   ```

### No Data Available

If training fails with "No data available":

1. Check date range in training script
2. Verify transactions exist in database:
   ```sql
   SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED';
   ```

3. Check fraud labels:
   ```sql
   SELECT COUNT(*) FROM security_alerts;
   SELECT COUNT(*) FROM bot_detection;
   ```

### Feature Engineering Errors

If features fail to compute:

1. Check database schema matches expected structure
2. Verify required tables exist
3. Check for NULL values in required columns

### Redis Connection Issues

If MAB state fails to save:

1. Check Redis is running:
   ```bash
   redis-cli ping
   ```

2. Check Redis configuration in `config.yaml`

## Production Deployment

### Automated Training

Set up scheduled training:

```bash
# Add to crontab
0 2 * * * cd /path/to/NFT-TICKETING/sprint3 && python ml_pipeline/train_fraud_model_db.py >> logs/training.log 2>&1
0 3 * * 0 cd /path/to/NFT-TICKETING/sprint3 && python ml_pipeline/train_mab_model.py >> logs/mab_training.log 2>&1
```

### Model Versioning

Models are versioned by filename:
- `fraud_model_v1.2.3.pkl`
- Update version in training script when retraining

### Model Updates

1. Train new model
2. Validate performance
3. Update model path in `config.yaml`:
   ```yaml
   ml:
     fraud_model_path: ml_pipeline/models/fraud_model_v1.2.4.pkl
     model_version: v1.2.4
   ```
4. Restart API services

## Next Steps

1. **Set up database connection** - Configure `config.yaml` or environment variables
2. **Run ETL pipeline** - Extract and transform data
3. **Train fraud model** - Run `train_fraud_model_db.py`
4. **Train MAB model** - Run `train_mab_model.py`
5. **Validate models** - Check metrics and test predictions
6. **Deploy** - Update config and restart services

## Additional Resources

- `sprint3/data_control/db_connection.py` - Database connection utilities
- `sprint3/data_control/etl_pipeline.py` - ETL pipeline implementation
- `sprint3/ml_pipeline/feature_engineering.py` - Feature engineering
- `sprint3/ml_pipeline/mab_pricing.py` - MAB model implementation


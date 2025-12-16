# Data Science Module

Production-ready data science infrastructure for the NFT Ticketing Platform.

## Structure

```
data_science/
├── config/              # Configuration files
│   └── model_configs/   # Individual model configurations
├── data/                # Data management
│   ├── raw/             # Raw data (gitignored)
│   ├── processed/       # Processed features
│   └── predictions/     # Model outputs
├── pipelines/           # ML Pipelines
│   └── training_pipeline.py
├── models/              # Model implementations
│   ├── risk_score.py
│   ├── bot_detection.py
│   ├── fair_price.py
│   ├── scalping_detection.py
│   ├── wash_trading.py
│   ├── recommender.py
│   ├── segmentation.py
│   ├── market_trend.py
│   └── decision_rule.py
├── notebooks/           # Jupyter notebooks for exploration
├── tests/               # Unit tests
├── artifacts/           # Trained model files (.joblib)
├── core.py              # Core utilities (DataLogger, KPICalculator, ABTestManager)
├── feature_store.py     # Feature engineering
└── evaluation_report.md # Model evaluation documentation
```

## Models

### 1. Risk Score Model
- **Type**: Random Forest Classifier
- **Purpose**: Detect high-risk transactions
- **Inputs**: Transaction amount, user transaction count
- **Output**: Risk score (0.0 - 1.0)

### 2. Bot Detection Model
- **Type**: Isolation Forest
- **Purpose**: Identify bot activity
- **Inputs**: Transaction velocity, patterns
- **Output**: Bot probability

### 3. Fair Price Model
- **Type**: Linear Regression
- **Purpose**: Predict fair market price
- **Inputs**: Event features, historical prices
- **Output**: Predicted fair price

### 4. Scalping Detection Model
- **Type**: Rule-based + ML
- **Purpose**: Detect ticket scalping
- **Inputs**: Purchase patterns, resale behavior
- **Output**: Scalping score

### 5. Wash Trading Model
- **Type**: Graph-based detection
- **Purpose**: Identify wash trading
- **Inputs**: Transaction network
- **Output**: Wash trading probability

### 6. Recommender System
- **Type**: Content-based filtering
- **Purpose**: Recommend events to users
- **Inputs**: User preferences, event categories
- **Output**: Recommended event list

### 7. User Segmentation
- **Type**: K-Means Clustering
- **Purpose**: Segment users by behavior
- **Inputs**: Transaction value, frequency
- **Output**: Cluster ID (0, 1, 2)

### 8. Market Trend Prediction
- **Type**: Linear Regression
- **Purpose**: Predict future trends
- **Inputs**: Time series data
- **Output**: Predicted trend

### 9. Decision Rule Engine
- **Type**: Statistical (Bollinger Bands)
- **Purpose**: Real-time anomaly detection
- **Inputs**: Value stream
- **Output**: NORMAL or ANOMALY

## Usage

### Training Models

```python
from backend.data_science.pipelines.training_pipeline import train_all

# Train all models
train_all()
```

### Using Models

```python
from backend.data_science.models.risk_score import risk_model

# Predict risk score
risk = risk_model.predict({
    "amount": 500,
    "user_tx_count": 3
})
```

### A/B Testing

```python
from backend.data_science.core import ab_test_manager

# Assign user to variant
variant = ab_test_manager.assign_variant("user_123", "pricing_test")
```

### KPI Tracking

```python
from backend.data_science.core import kpi_calculator

# Calculate conversion rate
conversion = kpi_calculator.conversion_rate()
```

## Integration

Models are integrated into the backend via:
- `backend/routers/ml_services.py` - API endpoints
- `backend/main.py` - Global instances (data_logger, kpi_calculator, ab_test_manager)

## Development

### Adding a New Model

1. Create model file in `models/`
2. Add config in `config/model_configs/`
3. Update `pipelines/training_pipeline.py`
4. Add tests in `tests/`
5. Update this README

### Running Tests

```bash
pytest backend/data_science/tests/
```

## Data Flow

```
Raw Data → Feature Engineering → Model Training → Artifacts
                                       ↓
                                  Inference API
                                       ↓
                                  Predictions
```

## Notes

- All models support fallback logic when dependencies are missing
- Models are trained on dummy data by default (fetch real data from Supabase in production)
- Artifacts are saved as `.joblib` files for fast loading

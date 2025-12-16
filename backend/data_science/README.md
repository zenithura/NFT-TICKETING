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

### 1. Risk Score Model (`risk_score.py`)
- **Algorithm**: **Random Forest Classifier**
- **Why**: Robust against overfitting and handles non-linear relationships well. Provides feature importance (SHAP values) to explain *why* a transaction is flagged.
- **Inputs**: Transaction amount, user transaction count, velocity.
- **Output**: Risk score (0.0 - 1.0).

### 2. Bot Detection Model (`bot_detection.py`)
- **Algorithm**: **Isolation Forest**
- **Why**: Unsupervised anomaly detection. Efficiently isolates "different" behavior (superhuman speed, perfect timing) without needing labeled bot data.
- **Inputs**: Transaction velocity, user agent score, IP reputation.
- **Output**: Bot probability and anomaly score.

### 3. Fair Price Model (`fair_price.py`)
- **Algorithm**: **Gradient Boosting Regressor**
- **Why**: Handles complex, non-linear interactions between features (e.g., popularity vs. days left) to predict continuous price values accurately in volatile markets.
- **Inputs**: Original price, popularity score, days left.
- **Output**: Predicted fair market price.

### 4. Scalping Detection Model (`scalping_detection.py`)
- **Algorithm**: **Logistic Regression**
- **Why**: Fast, interpretable binary classification. Outputs a probability score (0-1) perfect for setting clear thresholds on linear indicators like purchase count and holding time.
- **Inputs**: Purchase count, resale velocity, holding time.
- **Output**: Scalping probability.

### 5. Wash Trading Model (`wash_trading.py`)
- **Algorithm**: **Graph Cycle Detection (NetworkX)**
- **Why**: Wash trading is a topology problem (circular flow A->B->C->A). Graph traversal algorithms find these closed loops more effectively than statistical models.
- **Inputs**: Buyer ID, Seller ID, NFT ID.
- **Output**: Cycle detection path.

### 6. Recommender System (`recommender.py`)
- **Algorithm**: **Content-Based Filtering**
- **Why**: Solves the "Cold Start" problem for MVPs. Recommends items similar to user's history without needing massive collaborative datasets.
- **Inputs**: User preferred category.
- **Output**: List of recommended ticket IDs.

### 7. User Segmentation (`segmentation.py`)
- **Algorithm**: **K-Means Clustering**
- **Why**: Unsupervised grouping of users into distinct buckets (e.g., "Whales", "Casuals") based on behavioral distance.
- **Inputs**: Average transaction value, frequency.
- **Output**: Cluster ID (0, 1, 2).

### 8. Market Trend Prediction (`market_trend.py`)
- **Algorithm**: **Linear Regression**
- **Why**: Captures the general direction (slope) of the market efficiently. Computationally cheap and provides clear trend lines for dashboards.
- **Inputs**: Day index.
- **Output**: Predicted sales trend.

### 9. Decision Rule Engine (`decision_rule.py`)
- **Algorithm**: **Statistical Bollinger Bands**
- **Why**: Heuristic model for real-time monitoring. Extremely fast, requires no training, and instantly detects anomalies defined as deviations from the moving average.
- **Inputs**: Value stream (e.g., latency).
- **Output**: NORMAL or ANOMALY decision.

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

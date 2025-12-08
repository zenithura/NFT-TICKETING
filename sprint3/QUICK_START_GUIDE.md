# Sprint 3 Quick Start Guide

## Overview

Sprint 3 implementation is **complete** with all requirements satisfied. This guide helps you get started quickly.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Redis 7+ (or Docker)
- Docker & Docker Compose (optional, for services)

## Installation

```bash
cd sprint3
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in `sprint3/` directory:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ticketing
DB_USER=admin
DB_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Monitoring API
MONITORING_API_PORT=5002
```

Or use `config/config.yaml` for configuration.

## Start Services

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Fraud API on port 5001
- Monitoring Dashboard on port 8050

### Option 2: Manual Start

```bash
# Terminal 1: Fraud API
python api/fraud_api.py

# Terminal 2: Monitoring API
python monitoring/monitoring_api.py

# Terminal 3: Dashboard
python monitoring/dashboard.py
```

## Access Points

- **Fraud API**: http://localhost:5001
  - Health: http://localhost:5001/health
  - Predict: POST http://localhost:5001/api/v1/ml/predict/fraud
  
- **Monitoring API**: http://localhost:5002
  - KPIs: http://localhost:5002/api/v1/metrics/kpis
  - System Metrics: http://localhost:5002/api/v1/metrics/system
  - Alerts: http://localhost:5002/api/v1/alerts

- **Dashboard**: http://localhost:8050

## Quick Test

```bash
# Test Fraud API
curl -X POST http://localhost:5001/api/v1/ml/predict/fraud \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test_001",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "ticket_id": "evt_001",
    "price_paid": 50.00
  }'

# Test Monitoring API
curl http://localhost:5002/api/v1/metrics/kpis
```

## Run ETL Pipeline

```bash
python -c "
from data_control.etl_pipeline import get_etl_pipeline
pipeline = get_etl_pipeline()
pipeline.run_full_pipeline()
"
```

## Run Tests

```bash
pytest tests/ -v
```

## Key Components

### Data Science
- **KPIs**: `ml_pipeline/kpi_calculator.py`
- **Feature Engineering**: `ml_pipeline/feature_engineering.py`
- **ML Models**: `ml_pipeline/models_ensemble.py`
- **MAB Router**: `ml_pipeline/mab_pricing.py`
- **Model Logging**: `ml_pipeline/model_logging.py`

### Data Control
- **ETL Pipeline**: `data_control/etl_pipeline.py`
- **Retention Policy**: `data_control/data_retention.py`

### Monitoring & Security
- **Monitoring API**: `monitoring/monitoring_api.py`
- **Alert System**: `monitoring/alert_rules.py`
- **Dashboard**: `monitoring/dashboard.py`
- **SIEM/SOAR**: `security/siem_integration.py`
- **Rate Limiting**: `security/rate_limiter.py`

### Integration
- **Integration Layer**: `integration/integration_layer.py`

## Documentation

- **Complete Implementation**: `SPRINT3_IMPLEMENTATION_COMPLETE.md`
- **Threat Model**: `THREAT_MODEL.md`
- **Data Science Report**: `DS_REPORT.md`
- **Baseline KPIs**: `baseline_kpi_snapshot.json`

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `psql -U admin -d ticketing`
- Check connection settings in `.env` or `config/config.yaml`

### Redis Connection Issues
- Verify Redis is running: `redis-cli ping`
- Check Redis host/port settings

### Model Not Found
- Train the model first: `python ml_pipeline/train_fraud_model.py`
- Or use demo mode (will work with defaults)

## Next Steps

1. Review `SPRINT3_IMPLEMENTATION_COMPLETE.md` for full details
2. Run the dashboard and explore metrics
3. Integrate with your backend API
4. Configure alerts for your environment
5. Set up scheduled ETL jobs (cron/scheduler)

## Support

For issues or questions, refer to:
- Code documentation in each module
- `SPRINT3_IMPLEMENTATION_COMPLETE.md` for architecture details
- `THREAT_MODEL.md` for security considerations


# Sprint 3 Deployment Guide
## NFT Ticketing Platform - Data Science & Security Layer

**Version**: 1.0  
**Date**: 2025-11-28  
**Deployment Target**: Production (AWS)

---

## Prerequisites

### Infrastructure Requirements

| Component | Specification | Purpose |
|-----------|---------------|---------|
| **PostgreSQL** | AWS RDS db.r5.xlarge (4 vCPU, 32GB RAM) | Transaction data, features, audit logs |
| **Redis** | AWS ElastiCache cache.r5.large (2 vCPU, 13GB RAM) | Feature cache, rate limiting |
| **Application Server** | AWS ECS Fargate (2 vCPU, 4GB RAM) × 4 tasks | Fraud API, monitoring dashboard |
| **Web3 Provider** | Infura/Alchemy (2M requests/month) | Blockchain data extraction |
| **Storage** | AWS S3 (500GB) | Model artifacts, backups |

### Software Dependencies

```bash
# Python 3.11+
python --version  # Should be 3.11 or higher

# PostgreSQL 15+
psql --version

# Redis 7+
redis-cli --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Node.js 18+ (for smart contract interaction)
node --version
```

---

## Step 1: Environment Setup

### 1.1 Clone Repository

```bash
cd /home/mahammad/NFT-TICKETING
git checkout -b sprint3-deployment

# Verify sprint3 directory exists
ls -la sprint3/
```

### 1.2 Create Environment Variables

Create `.env` file in `sprint3/` directory:

```bash
cat > sprint3/.env << 'EOF'
# Database Configuration
DB_HOST=your-rds-endpoint.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=ticketing
DB_USER=admin
DB_PASSWORD=your-secure-password-here

# Redis Configuration
REDIS_HOST=your-elasticache-endpoint.cache.amazonaws.com
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Web3 Provider
INFURA_KEY=your-infura-api-key
ALCHEMY_KEY=your-alchemy-api-key
WEB3_PROVIDER=https://mainnet.infura.io/v3/${INFURA_KEY}

# Smart Contract
CONTRACT_ADDRESS=0x...  # Your deployed NFT ticketing contract

# Security
JWT_SECRET=your-jwt-secret-key-min-32-chars
ADMIN_MFA_SECRET=your-totp-secret

# Monitoring
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PAGERDUTY_API_KEY=your-pagerduty-key

# ML Model
MODEL_VERSION=v1.2.3
FRAUD_THRESHOLD_BLOCK=0.85
FRAUD_THRESHOLD_REVIEW=0.65

# Rate Limiting
RATE_LIMIT_GLOBAL=10000
RATE_LIMIT_IP=100
RATE_LIMIT_USER=500

# Environment
ENVIRONMENT=production
DEBUG=false
EOF

# Secure the .env file
chmod 600 sprint3/.env
```

### 1.3 Install Python Dependencies

```bash
cd sprint3/

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import xgboost, flask, dash, web3; print('All packages installed successfully')"
```

**requirements.txt**:
```
# Core
flask==3.0.0
flask-cors==4.0.0
flask-limiter==3.5.0
gunicorn==21.2.0

# Database
psycopg2-binary==2.9.9
redis==5.0.1
sqlalchemy==2.0.23

# ML & Data Science
xgboost==2.0.2
scikit-learn==1.3.2
pandas==2.1.4
numpy==1.26.2
shap==0.44.0

# Monitoring & Dashboards
dash==2.14.2
plotly==5.18.0
dash-bootstrap-components==1.5.0

# Blockchain
web3==6.11.3

# Security
pyotp==2.9.0
cryptography==41.0.7

# Utilities
pyyaml==6.0.1
python-dotenv==1.0.0
requests==2.31.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
```

---

## Step 2: Database Setup

### 2.1 Create Database Schema

```bash
# Connect to PostgreSQL
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Or use the provided script
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sprint3/sql/schema.sql
```

**schema.sql**:
```sql
-- Create tables
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    wallet_address VARCHAR(42) NOT NULL,
    event_id VARCHAR(64) NOT NULL,
    ticket_id VARCHAR(64),
    price_paid DECIMAL(18, 8),
    payment_method VARCHAR(32),
    is_resale BOOLEAN DEFAULT false,
    status VARCHAR(16),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_wallet ON transactions(wallet_address);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_transactions_event ON transactions(event_id);

CREATE TABLE IF NOT EXISTS fraud_predictions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) NOT NULL,
    fraud_score DECIMAL(5, 3),
    decision VARCHAR(16),
    features JSONB,
    model_version VARCHAR(16),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fraud_predictions_txn ON fraud_predictions(transaction_id);
CREATE INDEX idx_fraud_predictions_timestamp ON fraud_predictions(timestamp);

CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(32) NOT NULL,
    severity VARCHAR(16),
    source_ip VARCHAR(45),
    user_id VARCHAR(64),
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_security_events_type ON security_events(event_type);
CREATE INDEX idx_security_events_timestamp ON security_events(timestamp);

CREATE TABLE IF NOT EXISTS blacklisted_wallets (
    wallet_address VARCHAR(42) PRIMARY KEY,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_audit_log (
    id SERIAL PRIMARY KEY,
    admin_user VARCHAR(64),
    action VARCHAR(128),
    ip_address VARCHAR(45),
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Archive tables
CREATE TABLE IF NOT EXISTS transactions_archive (LIKE transactions INCLUDING ALL);
CREATE TABLE IF NOT EXISTS fraud_predictions_archive (LIKE fraud_predictions INCLUDING ALL);

-- Materialized views
CREATE MATERIALIZED VIEW kpi_hourly AS
SELECT 
    DATE_TRUNC('hour', t.timestamp) AS hour,
    COUNT(DISTINCT t.transaction_id) AS total_transactions,
    COUNT(DISTINCT t.wallet_address) AS unique_wallets,
    SUM(t.price_paid) AS total_revenue,
    AVG(fp.fraud_score) AS avg_fraud_score,
    SUM(CASE WHEN fp.decision = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked_count,
    SUM(CASE WHEN fp.decision = 'APPROVED' THEN 1 ELSE 0 END) AS approved_count
FROM transactions t
LEFT JOIN fraud_predictions fp ON t.transaction_id = fp.transaction_id
WHERE t.timestamp > NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC;

CREATE UNIQUE INDEX idx_kpi_hourly_hour ON kpi_hourly(hour);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO admin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO admin;
```

### 2.2 Load Initial Data (Optional)

```bash
# Load sample data for testing
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sprint3/sql/sample_data.sql
```

---

## Step 3: Train & Deploy ML Model

### 3.1 Train Fraud Detection Model

```bash
cd sprint3/ml_pipeline/

# Train model (uses historical data from database)
python train_fraud_model.py --output models/fraud_model_v1.2.3.pkl

# Evaluate model
python model_evaluation.py --model models/fraud_model_v1.2.3.pkl

# Expected output:
# AUC-ROC: 0.947
# AUC-PR: 0.823
# F1 Score: 0.81
# Model saved to models/fraud_model_v1.2.3.pkl
```

### 3.2 Upload Model to S3

```bash
# Upload trained model to S3 for version control
aws s3 cp ml_pipeline/models/fraud_model_v1.2.3.pkl \
  s3://nft-ticketing-models/fraud/v1.2.3/model.pkl

# Upload model metadata
aws s3 cp ml_pipeline/models/model_metadata.json \
  s3://nft-ticketing-models/fraud/v1.2.3/metadata.json
```

---

## Step 4: Deploy Services with Docker

### 4.1 Build Docker Images

```bash
cd sprint3/

# Build fraud API image
docker build -t nft-ticketing/fraud-api:v1.2.3 -f Dockerfile.fraud_api .

# Build monitoring dashboard image
docker build -t nft-ticketing/monitoring:v1.0.0 -f Dockerfile.monitoring .

# Verify images
docker images | grep nft-ticketing
```

**Dockerfile.fraud_api**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ml_pipeline/ ./ml_pipeline/
COPY api/ ./api/
COPY security/ ./security/
COPY config/ ./config/

# Download model from S3 (or copy local)
RUN mkdir -p ml_pipeline/models/
COPY ml_pipeline/models/fraud_model_v1.2.3.pkl ml_pipeline/models/

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "60", "api.fraud_api:app"]
```

### 4.2 Deploy with Docker Compose

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                  STATUS    PORTS
# sprint3-postgres-1    Up        0.0.0.0:5432->5432/tcp
# sprint3-redis-1       Up        0.0.0.0:6379->6379/tcp
# sprint3-fraud_api-1   Up        0.0.0.0:5001->5001/tcp
# sprint3-monitoring-1  Up        0.0.0.0:8050->8050/tcp

# Check logs
docker-compose logs -f fraud_api
```

### 4.3 Health Checks

```bash
# Test fraud API
curl http://localhost:5001/health
# Expected: {"status": "healthy", "model_version": "v1.2.3"}

# Test monitoring dashboard
curl http://localhost:8050/
# Expected: HTML response

# Test database connection
docker-compose exec fraud_api python -c "import psycopg2; conn = psycopg2.connect('dbname=ticketing user=admin host=postgres'); print('DB connected')"
```

---

## Step 5: Configure Cron Jobs

### 5.1 ETL Pipeline (Daily)

```bash
# Add to crontab
crontab -e

# Add these lines:
# Daily ETL at 02:00 UTC
0 2 * * * cd /home/mahammad/NFT-TICKETING/sprint3 && ./scripts/run_etl.sh >> /var/log/etl.log 2>&1

# Refresh materialized views every 5 minutes
*/5 * * * * psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_hourly;" >> /var/log/mv_refresh.log 2>&1

# Data retention enforcement (weekly, Sunday 03:00 UTC)
0 3 * * 0 cd /home/mahammad/NFT-TICKETING/sprint3 && python data_control/data_retention.py >> /var/log/retention.log 2>&1

# Model retraining (bi-weekly, Sunday 02:00 UTC)
0 2 */14 * * cd /home/mahammad/NFT-TICKETING/sprint3 && python ml_pipeline/train_fraud_model.py --auto-deploy >> /var/log/model_training.log 2>&1
```

### 5.2 Make Scripts Executable

```bash
chmod +x sprint3/scripts/run_etl.sh
chmod +x sprint3/scripts/deploy_model.sh
chmod +x sprint3/scripts/setup_monitoring.sh
```

---

## Step 6: Configure Monitoring & Alerts

### 6.1 Setup Alert Rules

```bash
# Configure alert rules
cp sprint3/config/alert_rules.yaml.example sprint3/config/alert_rules.yaml

# Edit thresholds as needed
vim sprint3/config/alert_rules.yaml
```

**alert_rules.yaml**:
```yaml
alerts:
  - name: fraud_rate_spike
    condition: fraud_rate > 0.03
    duration: 10m
    severity: high
    action: pagerduty
    
  - name: api_latency_high
    condition: p95_latency > 100
    duration: 5m
    severity: medium
    action: slack
    
  - name: model_drift
    condition: kl_divergence > 0.15
    duration: 1h
    severity: medium
    action: email
    
  - name: failed_login_attempts
    condition: failed_logins > 5
    duration: 5m
    severity: high
    action: block_ip
```

### 6.2 Start Monitoring Dashboard

```bash
# Access dashboard at http://localhost:8050
# Login with admin credentials (MFA required)

# For production, use reverse proxy (nginx):
sudo apt install nginx

# Configure nginx
sudo vim /etc/nginx/sites-available/monitoring

# Add:
server {
    listen 80;
    server_name monitoring.nft-ticketing.com;
    
    location / {
        proxy_pass http://localhost:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

sudo ln -s /etc/nginx/sites-available/monitoring /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 7: Integration with Existing Backend

### 7.1 Update Backend API to Call Fraud Detection

**Modify**: `frontend_with_backend/backend/routes/tickets.py`

```python
import requests
from flask import request, jsonify

FRAUD_API_URL = "http://localhost:5001/api/v1/ml/predict/fraud"

@app.route('/api/tickets/buy', methods=['POST'])
def buy_ticket():
    data = request.get_json()
    
    # Call fraud detection API
    fraud_check = requests.post(FRAUD_API_URL, json={
        'transaction_id': data['transaction_id'],
        'wallet_address': data['wallet_address'],
        'ticket_id': data['ticket_id'],
        'price_paid': data['price_paid'],
        'timestamp': datetime.now().isoformat()
    })
    
    fraud_result = fraud_check.json()
    
    # Handle decision
    if fraud_result['decision'] == 'BLOCKED':
        return jsonify({'error': 'Transaction blocked due to fraud risk'}), 403
    elif fraud_result['decision'] == 'MANUAL_REVIEW':
        return jsonify({'status': 'pending_review', 'message': 'Transaction requires manual review'}), 202
    elif fraud_result['decision'] == 'REQUIRE_2FA':
        return jsonify({'status': 'require_2fa', 'message': 'Please complete 2FA'}), 202
    
    # Proceed with purchase
    # ... existing purchase logic ...
    
    return jsonify({'status': 'success', 'ticket_id': ticket_id}), 200
```

### 7.2 Add Rate Limiting Middleware

**Create**: `frontend_with_backend/backend/middleware/rate_limiter.py`

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

redis_client = redis.Redis(host='localhost', port=6379)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["100 per minute"]
)

# Apply to app
from app import app
limiter.init_app(app)

# Apply specific limits
@app.route('/api/tickets/buy')
@limiter.limit("5 per minute")
def buy_ticket():
    # ...
```

---

## Step 8: Testing & Validation

### 8.1 Run Unit Tests

```bash
cd sprint3/

# Run all tests
pytest tests/ -v --cov=. --cov-report=html

# Expected output:
# ==================== test session starts ====================
# collected 47 items
#
# tests/test_fraud_api.py .................... [ 42%]
# tests/test_rate_limiter.py ............ [ 68%]
# tests/test_feature_engineering.py ............. [100%]
#
# ==================== 47 passed in 12.34s ====================
# Coverage: 87%

# View coverage report
open htmlcov/index.html
```

### 8.2 Integration Testing

```bash
# Test fraud API end-to-end
python tests/test_integration.py

# Test workflow:
# 1. Create test transaction
# 2. Call fraud API
# 3. Verify decision logic
# 4. Check database logging
# 5. Verify Redis cache updates
```

### 8.3 Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:5001

# Open http://localhost:8089
# Configure: 100 users, 10 spawn rate
# Run for 5 minutes
# Expected: p95 latency <100ms, 0 errors
```

---

## Step 9: Production Deployment (AWS)

### 9.1 Push Docker Images to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Tag images
docker tag nft-ticketing/fraud-api:v1.2.3 YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/fraud-api:v1.2.3
docker tag nft-ticketing/monitoring:v1.0.0 YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/monitoring:v1.0.0

# Push images
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/fraud-api:v1.2.3
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/monitoring:v1.0.0
```

### 9.2 Deploy to ECS

```bash
# Update ECS task definition
aws ecs register-task-definition --cli-input-json file://sprint3/aws/task-definition.json

# Update service
aws ecs update-service \
  --cluster nft-ticketing-cluster \
  --service fraud-api-service \
  --task-definition fraud-api:latest \
  --desired-count 4

# Verify deployment
aws ecs describe-services \
  --cluster nft-ticketing-cluster \
  --services fraud-api-service
```

### 9.3 Configure Load Balancer

```bash
# Create target group
aws elbv2 create-target-group \
  --name fraud-api-tg \
  --protocol HTTP \
  --port 5001 \
  --vpc-id vpc-xxxxx \
  --health-check-path /health

# Register targets (ECS tasks auto-register)
# Configure ALB listener rule to route /api/v1/ml/* to fraud-api-tg
```

---

## Step 10: Post-Deployment Verification

### 10.1 Smoke Tests

```bash
# Test production endpoint
curl https://api.nft-ticketing.com/api/v1/ml/predict/fraud \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test_001",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "ticket_id": "evt_001",
    "price_paid": 50.00
  }'

# Expected: {"fraud_score": 0.12, "decision": "APPROVED", ...}
```

### 10.2 Monitor Logs

```bash
# CloudWatch Logs
aws logs tail /ecs/fraud-api --follow

# Check for errors
aws logs filter-pattern /ecs/fraud-api --filter-pattern "ERROR"
```

### 10.3 Verify Metrics

```bash
# Access monitoring dashboard
open https://monitoring.nft-ticketing.com/admin

# Check:
# - API latency <50ms
# - Fraud detection rate >94%
# - No errors in last hour
# - All services healthy
```

---

## Rollback Procedure

If deployment fails:

```bash
# Rollback ECS service to previous task definition
aws ecs update-service \
  --cluster nft-ticketing-cluster \
  --service fraud-api-service \
  --task-definition fraud-api:PREVIOUS_VERSION

# Restore database from backup
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier ticketing-prod \
  --target-db-instance-identifier ticketing-prod-restored \
  --restore-time 2025-11-28T18:00:00Z

# Switch traffic back to old model
aws s3 cp s3://nft-ticketing-models/fraud/v1.2.2/model.pkl \
  ml_pipeline/models/fraud_model_v1.2.3.pkl
```

---

## Maintenance & Operations

### Daily Tasks
- ✅ Check monitoring dashboard for anomalies
- ✅ Review security event logs
- ✅ Verify ETL job completion

### Weekly Tasks
- ✅ Review model performance metrics
- ✅ Analyze false positive cases
- ✅ Update threat intelligence feeds

### Bi-Weekly Tasks
- ✅ Retrain fraud detection model
- ✅ Review and update alert thresholds
- ✅ Conduct security audit

### Monthly Tasks
- ✅ Review KPI trends vs. targets
- ✅ Optimize infrastructure costs
- ✅ Update documentation

---

## Troubleshooting

### Issue: High API Latency

**Symptoms**: p95 latency >100ms

**Diagnosis**:
```bash
# Check database query performance
psql -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check Redis cache hit rate
redis-cli INFO stats | grep keyspace_hits
```

**Solution**:
- Add database indexes
- Increase Redis cache TTL
- Scale ECS tasks

### Issue: Model Drift Detected

**Symptoms**: KL divergence >0.15

**Diagnosis**:
```bash
# Check feature distributions
python ml_pipeline/model_evaluation.py --check-drift
```

**Solution**:
- Trigger emergency model retraining
- Switch to ensemble model temporarily

### Issue: High False Positive Rate

**Symptoms**: False positive rate >2%

**Diagnosis**:
- Review flagged transactions manually
- Analyze feature importance shifts

**Solution**:
- Adjust fraud threshold (0.65 → 0.70)
- Add VIP whitelist
- Retrain with recent data

---

## Support & Escalation

**On-Call Engineer**: PagerDuty rotation  
**Slack Channel**: #sprint3-ops  
**Documentation**: https://wiki.nft-ticketing.com/sprint3  
**Runbooks**: `/home/mahammad/NFT-TICKETING/sprint3/runbooks/`

---

**Deployment Complete** ✅

All Sprint 3 components are now live in production!

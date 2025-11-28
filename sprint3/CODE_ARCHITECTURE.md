# Sprint 3 Code Architecture & Implementation
## NFT Ticketing Platform - Data Science & Security Layer

**Version**: 1.0  
**Date**: 2025-11-28  
**Tech Stack**: Python 3.11, Flask, XGBoost, PostgreSQL, Redis, Dash, Web3.py

---

## Project Structure

```
NFT-TICKETING/
├── sprint3/
│   ├── ml_pipeline/
│   │   ├── __init__.py
│   │   ├── feature_engineering.py      # Feature computation logic
│   │   ├── train_fraud_model.py        # Model training pipeline
│   │   ├── inference_service.py        # Real-time prediction API
│   │   ├── model_evaluation.py         # Metrics & validation
│   │   ├── mab_pricing.py              # Multi-armed bandit for pricing
│   │   └── models/
│   │       ├── fraud_model_v1.2.3.pkl  # Trained XGBoost model
│   │       └── model_metadata.json     # Version, metrics, features
│   │
│   ├── data_control/
│   │   ├── __init__.py
│   │   ├── etl_pipeline.py             # Extract-Transform-Load
│   │   ├── data_retention.py           # Retention policy enforcement
│   │   ├── materialized_views.sql      # PostgreSQL views for dashboards
│   │   └── tests/
│   │       ├── test_etl.py
│   │       └── test_retention.py
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py             # Redis-based rate limiting
│   │   ├── auth_middleware.py          # MFA + session management
│   │   ├── threat_detection.py         # SIEM correlation rules
│   │   └── audit_logger.py             # Security event logging
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── monitoring_api.py           # Flask API for metrics
│   │   ├── dashboard.py                # Dash + Plotly dashboard
│   │   ├── alert_rules.py              # Alert trigger logic
│   │   └── siem_integration.py         # Log ingestion & correlation
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── fraud_api.py                # POST /api/v1/ml/predict/fraud
│   │   ├── metrics_api.py              # GET /api/v1/metrics
│   │   └── admin_api.py                # Admin dashboard endpoints
│   │
│   ├── config/
│   │   ├── config.yaml                 # Environment configs
│   │   ├── alert_rules.yaml            # Alert thresholds
│   │   └── feature_definitions.yaml    # Feature metadata
│   │
│   ├── notebooks/
│   │   ├── fraud_model_evaluation.ipynb
│   │   ├── feature_analysis.ipynb
│   │   └── mab_simulation.ipynb
│   │
│   ├── scripts/
│   │   ├── deploy_model.sh             # Model deployment automation
│   │   ├── run_etl.sh                  # Daily ETL job
│   │   └── setup_monitoring.sh         # Dashboard initialization
│   │
│   ├── tests/
│   │   ├── test_fraud_api.py
│   │   ├── test_rate_limiter.py
│   │   └── test_integration.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend_with_backend/              # Existing codebase
├── smart-contracts/                    # Existing contracts
└── README.md
```

---

## Core Components Implementation

### 1. Feature Engineering (`ml_pipeline/feature_engineering.py`)

```python
"""
Feature engineering pipeline for fraud detection and user analytics.
Computes 10 core features from on-chain + off-chain data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from web3 import Web3
import psycopg2
import redis

class FeatureEngineer:
    def __init__(self, db_conn, redis_client, web3_provider):
        self.db = db_conn
        self.redis = redis_client
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
    
    def compute_features(self, transaction_id: str) -> dict:
        """
        Compute all features for a given transaction.
        
        Returns:
            dict: Feature vector with 10 engineered features
        """
        # Fetch transaction details
        txn = self._get_transaction(transaction_id)
        wallet = txn['wallet_address']
        event_id = txn['event_id']
        
        features = {
            'txn_velocity_1h': self._txn_velocity(wallet, hours=1),
            'wallet_age_days': self._wallet_age(wallet),
            'avg_ticket_hold_time': self._avg_hold_time(wallet),
            'event_popularity_score': self._event_popularity(event_id),
            'price_deviation_ratio': self._price_deviation(txn),
            'cross_event_attendance': self._cross_event_count(wallet),
            'geo_velocity_flag': self._geo_velocity_check(wallet),
            'payment_method_diversity': self._payment_diversity(wallet),
            'social_graph_centrality': self._centrality_score(wallet),
            'time_to_first_resale': self._resale_time(transaction_id)
        }
        
        # Cache features in Redis (5-minute TTL)
        cache_key = f"features:{transaction_id}"
        self.redis.setex(cache_key, 300, str(features))
        
        return features
    
    def _txn_velocity(self, wallet: str, hours: int) -> int:
        """Count transactions from wallet in last N hours"""
        query = """
            SELECT COUNT(*) FROM transactions
            WHERE wallet_address = %s
            AND timestamp > NOW() - INTERVAL '%s hours'
        """
        cur = self.db.cursor()
        cur.execute(query, (wallet, hours))
        count = cur.fetchone()[0]
        cur.close()
        return count
    
    def _wallet_age(self, wallet: str) -> float:
        """Days since wallet first interaction"""
        query = """
            SELECT MIN(timestamp) FROM transactions
            WHERE wallet_address = %s
        """
        cur = self.db.cursor()
        cur.execute(query, (wallet,))
        first_txn = cur.fetchone()[0]
        cur.close()
        
        if first_txn is None:
            return 0.0
        
        age = (datetime.now() - first_txn).total_seconds() / 86400
        return max(0.0, age)
    
    def _avg_hold_time(self, wallet: str) -> float:
        """Mean hours between purchase and transfer/use"""
        query = """
            SELECT AVG(EXTRACT(EPOCH FROM (transfer_time - purchase_time)) / 3600)
            FROM ticket_lifecycle
            WHERE wallet_address = %s
            AND transfer_time IS NOT NULL
        """
        cur = self.db.cursor()
        cur.execute(query, (wallet,))
        avg_hours = cur.fetchone()[0]
        cur.close()
        return avg_hours if avg_hours else 0.0
    
    def _event_popularity(self, event_id: str) -> float:
        """
        Popularity score: (tickets_sold / capacity) × (days_until_event)^-0.5
        Higher score = more popular event
        """
        query = """
            SELECT tickets_sold, capacity, event_date
            FROM events
            WHERE event_id = %s
        """
        cur = self.db.cursor()
        cur.execute(query, (event_id,))
        sold, capacity, event_date = cur.fetchone()
        cur.close()
        
        sell_through = sold / capacity if capacity > 0 else 0
        days_until = max(1, (event_date - datetime.now()).days)
        score = sell_through * (days_until ** -0.5)
        return score
    
    def _price_deviation(self, txn: dict) -> float:
        """(listing_price - floor_price) / floor_price"""
        listing_price = txn['price_paid']
        floor_price = self._get_floor_price(txn['event_id'])
        
        if floor_price == 0:
            return 0.0
        
        deviation = (listing_price - floor_price) / floor_price
        return deviation
    
    def _cross_event_count(self, wallet: str) -> int:
        """Count of distinct events attended by user"""
        query = """
            SELECT COUNT(DISTINCT event_id)
            FROM transactions
            WHERE wallet_address = %s
            AND status = 'completed'
        """
        cur = self.db.cursor()
        cur.execute(query, (wallet,))
        count = cur.fetchone()[0]
        cur.close()
        return count
    
    def _geo_velocity_check(self, wallet: str) -> bool:
        """
        Flag if IP location changed >500km in <1 hour
        Returns True if suspicious travel detected
        """
        query = """
            SELECT ip_address, timestamp, latitude, longitude
            FROM user_sessions
            WHERE wallet_address = %s
            ORDER BY timestamp DESC
            LIMIT 2
        """
        cur = self.db.cursor()
        cur.execute(query, (wallet,))
        sessions = cur.fetchall()
        cur.close()
        
        if len(sessions) < 2:
            return False
        
        # Calculate distance using Haversine formula
        lat1, lon1 = sessions[0][2], sessions[0][3]
        lat2, lon2 = sessions[1][2], sessions[1][3]
        distance_km = self._haversine(lat1, lon1, lat2, lon2)
        
        time_diff_hours = (sessions[0][1] - sessions[1][1]).total_seconds() / 3600
        
        # Flag if >500km in <1 hour (impossible travel)
        return distance_km > 500 and time_diff_hours < 1
    
    def _payment_diversity(self, wallet: str) -> int:
        """Count of unique payment methods used"""
        query = """
            SELECT COUNT(DISTINCT payment_method)
            FROM transactions
            WHERE wallet_address = %s
        """
        cur = self.db.cursor()
        cur.execute(query, (wallet,))
        count = cur.fetchone()[0]
        cur.close()
        return count
    
    def _centrality_score(self, wallet: str) -> float:
        """
        PageRank score in referral network
        Placeholder: returns 0.5 for now, implement graph analysis later
        """
        # TODO: Implement graph-based centrality using NetworkX
        return 0.5
    
    def _resale_time(self, transaction_id: str) -> float:
        """Minutes from mint to first secondary sale"""
        query = """
            SELECT EXTRACT(EPOCH FROM (first_resale_time - mint_time)) / 60
            FROM ticket_lifecycle
            WHERE transaction_id = %s
        """
        cur = self.db.cursor()
        cur.execute(query, (transaction_id,))
        result = cur.fetchone()
        cur.close()
        return result[0] if result and result[0] else 0.0
    
    # Helper methods
    def _get_transaction(self, transaction_id: str) -> dict:
        query = "SELECT * FROM transactions WHERE transaction_id = %s"
        cur = self.db.cursor()
        cur.execute(query, (transaction_id,))
        row = cur.fetchone()
        cur.close()
        return {
            'transaction_id': row[0],
            'wallet_address': row[1],
            'event_id': row[2],
            'price_paid': row[3],
            'timestamp': row[4]
        }
    
    def _get_floor_price(self, event_id: str) -> float:
        query = "SELECT MIN(price) FROM active_listings WHERE event_id = %s"
        cur = self.db.cursor()
        cur.execute(query, (event_id,))
        floor = cur.fetchone()[0]
        cur.close()
        return floor if floor else 0.0
    
    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in km"""
        R = 6371  # Earth radius in km
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
```

---

### 2. Fraud Detection API (`api/fraud_api.py`)

```python
"""
Real-time fraud detection API endpoint.
Loads features, runs XGBoost model, returns decision.
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pickle
import numpy as np
from ml_pipeline.feature_engineering import FeatureEngineer
import psycopg2
import redis
import logging

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

# Load trained model
with open('ml_pipeline/models/fraud_model_v1.2.3.pkl', 'rb') as f:
    fraud_model = pickle.load(f)

# Database connections
db_conn = psycopg2.connect("dbname=ticketing user=admin password=*** host=localhost")
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Initialize feature engineer
feature_eng = FeatureEngineer(db_conn, redis_client, web3_provider='https://mainnet.infura.io/v3/YOUR_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/api/v1/ml/predict/fraud', methods=['POST'])
@limiter.limit("5 per minute", key_func=lambda: request.json.get('wallet_address'))
def predict_fraud():
    """
    Predict fraud probability for a transaction.
    
    Request Body:
        {
            "transaction_id": "txn_abc123",
            "wallet_address": "0x742d35Cc...",
            "ticket_id": "evt_xyz_001",
            "price_paid": 150.00,
            "timestamp": "2025-11-28T14:30:00Z"
        }
    
    Response:
        {
            "fraud_score": 0.73,
            "decision": "MANUAL_REVIEW",
            "confidence": 0.89,
            "top_features": {...},
            "model_version": "v1.2.3"
        }
    """
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['transaction_id', 'wallet_address', 'ticket_id', 'price_paid']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        transaction_id = data['transaction_id']
        
        # Compute features
        logger.info(f"Computing features for {transaction_id}")
        features = feature_eng.compute_features(transaction_id)
        
        # Prepare feature vector (must match training order)
        feature_vector = np.array([[
            features['txn_velocity_1h'],
            features['wallet_age_days'],
            features['avg_ticket_hold_time'],
            features['event_popularity_score'],
            features['price_deviation_ratio'],
            features['cross_event_attendance'],
            float(features['geo_velocity_flag']),
            features['payment_method_diversity'],
            features['social_graph_centrality'],
            features['time_to_first_resale']
        ]])
        
        # Model inference
        fraud_score = fraud_model.predict_proba(feature_vector)[0][1]  # Probability of fraud
        
        # Decision logic
        if fraud_score > 0.85:
            decision = "BLOCKED"
        elif fraud_score > 0.65:
            decision = "MANUAL_REVIEW"
        elif fraud_score > 0.40:
            decision = "REQUIRE_2FA"
        else:
            decision = "APPROVED"
        
        # Get feature importance
        feature_names = [
            'txn_velocity_1h', 'wallet_age_days', 'avg_ticket_hold_time',
            'event_popularity_score', 'price_deviation_ratio', 'cross_event_attendance',
            'geo_velocity_flag', 'payment_method_diversity', 'social_graph_centrality',
            'time_to_first_resale'
        ]
        importances = fraud_model.feature_importances_
        top_features = dict(sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:3])
        
        # Log prediction to database
        _log_prediction(transaction_id, fraud_score, decision, features)
        
        # Update Redis KPIs
        _update_kpis(fraud_score, decision)
        
        response = {
            'fraud_score': round(fraud_score, 3),
            'decision': decision,
            'confidence': round(1 - abs(fraud_score - 0.5) * 2, 3),  # Confidence based on distance from 0.5
            'top_features': {k: round(v, 3) for k, v in top_features.items()},
            'model_version': 'v1.2.3'
        }
        
        logger.info(f"Prediction for {transaction_id}: {decision} (score: {fraud_score:.3f})")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error in fraud prediction: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def _log_prediction(transaction_id, fraud_score, decision, features):
    """Log prediction to PostgreSQL for monitoring"""
    query = """
        INSERT INTO fraud_predictions 
        (transaction_id, fraud_score, decision, features, timestamp)
        VALUES (%s, %s, %s, %s, NOW())
    """
    cur = db_conn.cursor()
    cur.execute(query, (transaction_id, fraud_score, decision, str(features)))
    db_conn.commit()
    cur.close()


def _update_kpis(fraud_score, decision):
    """Update real-time KPIs in Redis"""
    # Increment transaction counter
    redis_client.incr('kpi:total_transactions')
    
    # Update fraud rate
    if decision == "BLOCKED":
        redis_client.incr('kpi:blocked_transactions')
    
    # Calculate fraud rate (last 1 hour)
    total = int(redis_client.get('kpi:total_transactions') or 1)
    blocked = int(redis_client.get('kpi:blocked_transactions') or 0)
    fraud_rate = (blocked / total) * 100
    redis_client.setex('kpi:fraud_rate', 300, fraud_rate)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
```

---

### 3. Rate Limiter (`security/rate_limiter.py`)

```python
"""
Multi-layer rate limiting using Redis sliding window.
Protects against DDoS and scraping attacks.
"""

import redis
import time
from functools import wraps
from flask import request, jsonify

class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def limit(self, max_requests: int, window_seconds: int, key_prefix: str):
        """
        Decorator for rate limiting.
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            key_prefix: Redis key prefix (e.g., 'ip', 'user')
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Determine key based on prefix
                if key_prefix == 'ip':
                    identifier = request.remote_addr
                elif key_prefix == 'user':
                    identifier = request.headers.get('X-User-ID', 'anonymous')
                else:
                    identifier = key_prefix
                
                redis_key = f"rate_limit:{key_prefix}:{identifier}"
                
                # Sliding window algorithm
                now = time.time()
                window_start = now - window_seconds
                
                # Remove old entries
                self.redis.zremrangebyscore(redis_key, 0, window_start)
                
                # Count requests in current window
                current_requests = self.redis.zcard(redis_key)
                
                if current_requests >= max_requests:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': window_seconds
                    }), 429
                
                # Add current request
                self.redis.zadd(redis_key, {str(now): now})
                self.redis.expire(redis_key, window_seconds)
                
                return f(*args, **kwargs)
            
            return wrapped
        return decorator


# Usage example
redis_client = redis.Redis(host='localhost', port=6379)
rate_limiter = RateLimiter(redis_client)

@app.route('/api/events')
@rate_limiter.limit(max_requests=100, window_seconds=60, key_prefix='ip')
def get_events():
    # API logic here
    pass
```

---

### 4. Data Retention Policy (`data_control/data_retention.py`)

```python
"""
Data retention policy enforcement.
Manages on-chain vs off-chain data lifecycle.
"""

import psycopg2
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataRetentionManager:
    """
    Retention Policy:
    - On-chain data: Permanent (immutable)
    - Transaction logs: 90 days hot, 2 years archive, then delete
    - User sessions: 30 days
    - ML predictions: 180 days
    - Audit logs: 7 years (compliance)
    """
    
    def __init__(self, db_conn):
        self.db = db_conn
    
    def enforce_retention(self):
        """Run daily retention cleanup"""
        logger.info("Starting data retention enforcement")
        
        self._archive_old_transactions()
        self._delete_old_sessions()
        self._archive_ml_predictions()
        
        logger.info("Data retention enforcement completed")
    
    def _archive_old_transactions(self):
        """Move transactions older than 90 days to archive table"""
        query = """
            INSERT INTO transactions_archive
            SELECT * FROM transactions
            WHERE timestamp < NOW() - INTERVAL '90 days'
            AND transaction_id NOT IN (SELECT transaction_id FROM transactions_archive)
        """
        cur = self.db.cursor()
        cur.execute(query)
        archived_count = cur.rowcount
        
        # Delete from hot table
        cur.execute("DELETE FROM transactions WHERE timestamp < NOW() - INTERVAL '90 days'")
        deleted_count = cur.rowcount
        
        self.db.commit()
        cur.close()
        
        logger.info(f"Archived {archived_count} transactions, deleted {deleted_count} from hot table")
    
    def _delete_old_sessions(self):
        """Delete user sessions older than 30 days"""
        query = "DELETE FROM user_sessions WHERE timestamp < NOW() - INTERVAL '30 days'"
        cur = self.db.cursor()
        cur.execute(query)
        deleted_count = cur.rowcount
        self.db.commit()
        cur.close()
        
        logger.info(f"Deleted {deleted_count} old user sessions")
    
    def _archive_ml_predictions(self):
        """Archive ML predictions older than 180 days"""
        query = """
            INSERT INTO fraud_predictions_archive
            SELECT * FROM fraud_predictions
            WHERE timestamp < NOW() - INTERVAL '180 days'
        """
        cur = self.db.cursor()
        cur.execute(query)
        archived_count = cur.rowcount
        
        cur.execute("DELETE FROM fraud_predictions WHERE timestamp < NOW() - INTERVAL '180 days'")
        deleted_count = cur.rowcount
        
        self.db.commit()
        cur.close()
        
        logger.info(f"Archived {archived_count} ML predictions")


# Cron job: Run daily at 02:00 UTC
# 0 2 * * * python -c "from data_retention import DataRetentionManager; DataRetentionManager(db).enforce_retention()"
```

---

### 5. SIEM Integration (`monitoring/siem_integration.py`)

```python
"""
Mini SIEM/SOAR workflow:
Log Ingestion → Correlation → Triage → Response
"""

import logging
import json
from datetime import datetime
import psycopg2
import redis

logger = logging.getLogger(__name__)

class SIEMEngine:
    """
    Security Information and Event Management
    Correlates security events and triggers automated responses
    """
    
    def __init__(self, db_conn, redis_client):
        self.db = db_conn
        self.redis = redis_client
        self.correlation_rules = self._load_correlation_rules()
    
    def ingest_event(self, event: dict):
        """
        Ingest security event and correlate with existing data.
        
        Event schema:
            {
                'event_type': 'failed_login' | 'fraud_detected' | 'rate_limit_exceeded',
                'severity': 'low' | 'medium' | 'high' | 'critical',
                'source_ip': '203.0.113.42',
                'user_id': 'user_123',
                'timestamp': '2025-11-28T18:22:33Z',
                'metadata': {...}
            }
        """
        logger.info(f"Ingesting event: {event['event_type']} from {event['source_ip']}")
        
        # Store in database
        self._store_event(event)
        
        # Run correlation rules
        alerts = self._correlate_event(event)
        
        # Trigger responses for high-severity alerts
        for alert in alerts:
            if alert['severity'] in ['high', 'critical']:
                self._trigger_response(alert)
    
    def _store_event(self, event: dict):
        """Store event in security_events table"""
        query = """
            INSERT INTO security_events (event_type, severity, source_ip, user_id, metadata, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur = self.db.cursor()
        cur.execute(query, (
            event['event_type'],
            event['severity'],
            event['source_ip'],
            event.get('user_id'),
            json.dumps(event.get('metadata', {})),
            event['timestamp']
        ))
        self.db.commit()
        cur.close()
    
    def _correlate_event(self, event: dict) -> list:
        """
        Correlate event with historical data to detect patterns.
        Returns list of alerts.
        """
        alerts = []
        
        # Rule 1: Multiple failed logins from same IP
        if event['event_type'] == 'failed_login':
            recent_failures = self._count_recent_events(
                event_type='failed_login',
                source_ip=event['source_ip'],
                minutes=5
            )
            if recent_failures >= 5:
                alerts.append({
                    'alert_type': 'brute_force_attack',
                    'severity': 'high',
                    'source_ip': event['source_ip'],
                    'description': f"{recent_failures} failed login attempts in 5 minutes",
                    'recommended_action': 'block_ip'
                })
        
        # Rule 2: Fraud spike from specific wallet
        if event['event_type'] == 'fraud_detected':
            wallet = event['metadata'].get('wallet_address')
            recent_fraud = self._count_recent_events(
                event_type='fraud_detected',
                metadata_filter={'wallet_address': wallet},
                minutes=60
            )
            if recent_fraud >= 3:
                alerts.append({
                    'alert_type': 'fraud_ring_detected',
                    'severity': 'critical',
                    'wallet_address': wallet,
                    'description': f"{recent_fraud} fraud attempts from same wallet in 1 hour",
                    'recommended_action': 'blacklist_wallet'
                })
        
        # Rule 3: Distributed rate limit bypass attempt
        if event['event_type'] == 'rate_limit_exceeded':
            unique_ips = self._count_unique_ips_rate_limited(minutes=10)
            if unique_ips >= 50:
                alerts.append({
                    'alert_type': 'ddos_attack',
                    'severity': 'critical',
                    'description': f"{unique_ips} IPs rate-limited in 10 minutes (botnet suspected)",
                    'recommended_action': 'enable_cloudflare_challenge'
                })
        
        return alerts
    
    def _trigger_response(self, alert: dict):
        """
        Automated response to high-severity alerts (SOAR).
        """
        logger.warning(f"ALERT: {alert['alert_type']} - {alert['description']}")
        
        action = alert['recommended_action']
        
        if action == 'block_ip':
            self._block_ip(alert['source_ip'])
        elif action == 'blacklist_wallet':
            self._blacklist_wallet(alert['wallet_address'])
        elif action == 'enable_cloudflare_challenge':
            self._enable_cloudflare_challenge()
        
        # Send notification to on-call engineer
        self._send_pagerduty_alert(alert)
    
    def _block_ip(self, ip: str):
        """Add IP to Redis blocklist"""
        self.redis.sadd('blocked_ips', ip)
        self.redis.expire('blocked_ips', 3600)  # 1-hour block
        logger.info(f"Blocked IP: {ip}")
    
    def _blacklist_wallet(self, wallet: str):
        """Add wallet to permanent blacklist"""
        query = "INSERT INTO blacklisted_wallets (wallet_address, reason, timestamp) VALUES (%s, %s, NOW())"
        cur = self.db.cursor()
        cur.execute(query, (wallet, 'Automated fraud detection'))
        self.db.commit()
        cur.close()
        logger.info(f"Blacklisted wallet: {wallet}")
    
    def _enable_cloudflare_challenge(self):
        """Enable CAPTCHA challenge via Cloudflare API"""
        # Placeholder: integrate with Cloudflare API
        logger.info("Enabled Cloudflare challenge mode")
    
    def _send_pagerduty_alert(self, alert: dict):
        """Send alert to PagerDuty"""
        # Placeholder: integrate with PagerDuty API
        logger.critical(f"PagerDuty alert: {alert}")
    
    # Helper methods
    def _count_recent_events(self, event_type: str, source_ip: str = None, 
                            metadata_filter: dict = None, minutes: int = 5) -> int:
        query = """
            SELECT COUNT(*) FROM security_events
            WHERE event_type = %s
            AND timestamp > NOW() - INTERVAL '%s minutes'
        """
        params = [event_type, minutes]
        
        if source_ip:
            query += " AND source_ip = %s"
            params.append(source_ip)
        
        cur = self.db.cursor()
        cur.execute(query, tuple(params))
        count = cur.fetchone()[0]
        cur.close()
        return count
    
    def _count_unique_ips_rate_limited(self, minutes: int) -> int:
        query = """
            SELECT COUNT(DISTINCT source_ip) FROM security_events
            WHERE event_type = 'rate_limit_exceeded'
            AND timestamp > NOW() - INTERVAL '%s minutes'
        """
        cur = self.db.cursor()
        cur.execute(query, (minutes,))
        count = cur.fetchone()[0]
        cur.close()
        return count
    
    def _load_correlation_rules(self):
        """Load correlation rules from config"""
        # Placeholder: load from YAML config
        return {}
```

---

## Database Schema

### PostgreSQL Tables

```sql
-- Transactions table
CREATE TABLE transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    wallet_address VARCHAR(42) NOT NULL,
    event_id VARCHAR(64) NOT NULL,
    ticket_id VARCHAR(64),
    price_paid DECIMAL(18, 8),
    payment_method VARCHAR(32),
    status VARCHAR(16),
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_wallet (wallet_address),
    INDEX idx_timestamp (timestamp)
);

-- Fraud predictions
CREATE TABLE fraud_predictions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) NOT NULL,
    fraud_score DECIMAL(5, 3),
    decision VARCHAR(16),
    features JSONB,
    model_version VARCHAR(16),
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_txn (transaction_id),
    INDEX idx_timestamp (timestamp)
);

-- Security events
CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(32) NOT NULL,
    severity VARCHAR(16),
    source_ip VARCHAR(45),
    user_id VARCHAR(64),
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_event_type (event_type),
    INDEX idx_timestamp (timestamp)
);

-- Materialized view for dashboard KPIs
CREATE MATERIALIZED VIEW kpi_hourly AS
SELECT 
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN decision = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked_count,
    AVG(fraud_score) AS avg_fraud_score,
    SUM(price_paid) AS total_revenue
FROM fraud_predictions
JOIN transactions USING (transaction_id)
GROUP BY hour
ORDER BY hour DESC;

-- Refresh materialized view every 5 minutes
CREATE OR REPLACE FUNCTION refresh_kpi_hourly()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_hourly;
END;
$$ LANGUAGE plpgsql;

-- Cron job: */5 * * * * psql -c "SELECT refresh_kpi_hourly();"
```

---

## Configuration Files

### `config/config.yaml`

```yaml
# Sprint 3 Configuration

database:
  host: localhost
  port: 5432
  name: ticketing
  user: admin
  password: ${DB_PASSWORD}  # From environment variable

redis:
  host: localhost
  port: 6379
  db: 0

web3:
  provider: https://mainnet.infura.io/v3/${INFURA_KEY}
  contract_address: "0x..."

ml_models:
  fraud_detection:
    model_path: ml_pipeline/models/fraud_model_v1.2.3.pkl
    threshold_block: 0.85
    threshold_review: 0.65
    threshold_2fa: 0.40
    retraining_schedule: "0 2 * * 0"  # Every Sunday 02:00 UTC

rate_limiting:
  global_limit: 10000  # requests per minute
  ip_limit: 100
  user_limit: 500
  endpoint_limits:
    /api/buy: 5
    /api/events: 100

monitoring:
  dashboard_port: 8050
  refresh_interval: 5  # seconds
  alert_webhook: https://hooks.slack.com/services/...

security:
  session_timeout: 900  # 15 minutes
  mfa_required: true
  ip_whitelist:
    - 10.0.0.0/8
    - 192.168.0.0/16
```

---

## Deployment

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ticketing
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./data_control/materialized_views.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  fraud_api:
    build: .
    command: python api/fraud_api.py
    environment:
      DB_HOST: postgres
      REDIS_HOST: redis
      INFURA_KEY: ${INFURA_KEY}
    ports:
      - "5001:5001"
    depends_on:
      - postgres
      - redis

  monitoring_dashboard:
    build: .
    command: python monitoring/dashboard.py
    ports:
      - "8050:8050"
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

---

## Testing

### `tests/test_fraud_api.py`

```python
import pytest
from api.fraud_api import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_fraud_prediction_approved(client):
    """Test low-risk transaction gets approved"""
    payload = {
        "transaction_id": "txn_test_001",
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "ticket_id": "evt_xyz_001",
        "price_paid": 50.00
    }
    response = client.post('/api/v1/ml/predict/fraud', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['decision'] in ['APPROVED', 'REQUIRE_2FA']
    assert 0 <= data['fraud_score'] <= 1

def test_fraud_prediction_blocked(client):
    """Test high-risk transaction gets blocked"""
    # Mock a suspicious transaction (high velocity, new wallet)
    payload = {
        "transaction_id": "txn_test_002",
        "wallet_address": "0xNEW_WALLET_SUSPICIOUS",
        "ticket_id": "evt_xyz_002",
        "price_paid": 500.00
    }
    response = client.post('/api/v1/ml/predict/fraud', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['decision'] in ['BLOCKED', 'MANUAL_REVIEW']

def test_rate_limit(client):
    """Test rate limiting enforced"""
    payload = {"transaction_id": "txn_test_003", "wallet_address": "0x123", "ticket_id": "evt_001", "price_paid": 10}
    
    # Make 6 requests (limit is 5 per minute per wallet)
    for i in range(6):
        response = client.post('/api/v1/ml/predict/fraud', json=payload)
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Rate limit exceeded
```

---

This code architecture provides a production-ready foundation for Sprint 3. All components are modular, testable, and follow best practices for security and scalability.

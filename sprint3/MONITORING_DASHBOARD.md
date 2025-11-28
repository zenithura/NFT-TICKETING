# Monitoring Dashboard Blueprint
## Real-Time Security & Performance Monitoring

**Tech Stack**: Dash (Plotly) + Bootstrap + Redis + PostgreSQL  
**Refresh Rate**: 5 seconds (live metrics), 1 minute (aggregated stats)  
**Access**: `/admin/monitoring` (MFA required)

---

## Dashboard Layout

### Top Navigation Bar
```
┌─────────────────────────────────────────────────────────────────┐
│ 🎫 NFT Ticketing Platform  │  Monitoring Dashboard  │  🔴 LIVE  │
│ Last Updated: 2025-11-28 18:22:33 UTC                          │
└─────────────────────────────────────────────────────────────────┘
```

### Section 1: Key Performance Indicators (KPIs)

**Layout**: 4-column grid with metric cards

```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ 📊 Transactions  │ 🚨 Fraud Rate    │ ⚡ API Latency   │ 💰 Revenue/Hour  │
│                  │                  │                  │                  │
│    1,247         │    1.8%          │    45ms          │    $12,450       │
│  ▲ +12% (1h)     │  ▼ -0.3% (1h)    │  ▲ +5ms (1h)     │  ▲ +8% (1h)      │
│                  │                  │                  │                  │
│ Target: 1000/h   │ Target: <2%      │ Target: <50ms    │ Baseline: $11.5k │
│ Status: ✅       │ Status: ✅       │ Status: ⚠️       │ Status: ✅       │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

**KPI Definitions**:

1. **Transactions/Hour**: Total ticket purchases + transfers in rolling 1h window
   - **Alert**: <500/h during peak hours (18:00–22:00 UTC)
   
2. **Fraud Detection Rate**: (Blocked transactions / Total transactions) × 100
   - **Alert**: >3% (too many false positives) OR <0.5% (model may be failing)
   
3. **API Latency (p95)**: 95th percentile response time for `/api/v1/ml/predict/fraud`
   - **Alert**: >100ms (impacts user experience)
   
4. **Revenue per Hour**: Sum of ticket sales + platform fees
   - **Alert**: <$5k during event launch windows

---

### Section 2: Real-Time Fraud Detection

**Layout**: Time-series chart + live feed

```
┌─────────────────────────────────────────────────────────────────┐
│ Fraud Score Distribution (Last 1 Hour)                         │
│                                                                 │
│  1.0 ┤                                    ●                     │
│  0.9 ┤                              ●  ●  ●                     │
│  0.8 ┤         🔴 BLOCKED ZONE      ●  ●                        │
│  0.7 ┤─────────────────────────────●──────────                 │
│  0.6 ┤         🟡 REVIEW ZONE    ● ●                            │
│  0.5 ┤                          ●                               │
│  0.4 ┤─────────────────────────●──────────                     │
│  0.3 ┤         🟢 APPROVED    ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●  │
│  0.2 ┤                      ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●  │
│  0.1 ┤                    ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●  │
│      └────────────────────────────────────────────────────────▶│
│       17:00  17:15  17:30  17:45  18:00  18:15  18:22         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🚨 Recent High-Risk Transactions                               │
├──────────┬─────────────┬───────┬──────────┬────────────────────┤
│ Time     │ Txn ID      │ Score │ Decision │ Top Feature        │
├──────────┼─────────────┼───────┼──────────┼────────────────────┤
│ 18:22:15 │ txn_a7f3... │ 0.91  │ BLOCKED  │ txn_velocity_1h=12 │
│ 18:21:03 │ txn_b2e1... │ 0.78  │ REVIEW   │ price_deviation=2.3│
│ 18:19:47 │ txn_c9d4... │ 0.69  │ REVIEW   │ wallet_age=0.5d    │
│ 18:18:22 │ txn_d1a8... │ 0.88  │ BLOCKED  │ geo_velocity=true  │
└──────────┴─────────────┴───────┴──────────┴────────────────────┘
```

---

### Section 3: API Rate Limiting & Traffic

**Layout**: Dual charts (requests/min + top IPs)

```
┌──────────────────────────────────────┬──────────────────────────┐
│ API Requests per Minute              │ Top 5 IPs (Last 5 Min)   │
│                                      │                          │
│  500 ┤           ╭──╮                │ 1. 203.0.113.42  (487)   │
│  400 ┤       ╭───╯  ╰─╮              │ 2. 198.51.100.7  (312)   │
│  300 ┤   ╭───╯        ╰──╮           │ 3. 192.0.2.156   (289)   │
│  200 ┤───╯               ╰───        │ 4. 203.0.113.89  (201)   │
│  100 ┤                               │ 5. 198.51.100.23 (178)   │
│      └──────────────────────────────▶│                          │
│       18:15    18:18    18:21        │ 🔴 Rate Limited: 3 IPs   │
└──────────────────────────────────────┴──────────────────────────┘

Rate Limit Status:
  ✅ Global: 4,523 / 10,000 req/min (45%)
  ⚠️  IP 203.0.113.42: 98 / 100 req/min (NEAR LIMIT)
  🔴 IP 198.51.100.7: BLOCKED (exceeded 100 req/min)
```

---

### Section 4: Model Performance Metrics

**Layout**: Confusion matrix + drift monitoring

```
┌─────────────────────────────────────────────────────────────────┐
│ Model Performance (Last 24 Hours)                              │
│                                                                 │
│ Confusion Matrix:                  Feature Drift Score:        │
│                Predicted                                        │
│              Fraud  Legit          0.12 ┤     ●               │
│ Actual Fraud   142     18          0.10 ┤   ●   ●             │
│        Legit    89  11,751         0.08 ┤ ●       ●           │
│                                    0.06 ┤           ●         │
│ Precision: 0.614                   0.04 ┤             ● ●     │
│ Recall:    0.888                        └─────────────────────▶│
│ F1 Score:  0.726                         Mon Tue Wed Thu Fri  │
│                                                                 │
│ ⚠️  WARNING: Precision dropped 8% from baseline (0.67)         │
│ 📋 Action: Schedule model retraining (next: Sunday 02:00 UTC)  │
└─────────────────────────────────────────────────────────────────┘
```

**Drift Monitoring**:
- **KL Divergence** between current week vs. training data distribution
- **Threshold**: 0.15 (triggers alert)
- **Current**: 0.09 (healthy)

---

### Section 5: System Health

**Layout**: Service status grid + resource usage

```
┌─────────────────────────────────────────────────────────────────┐
│ Service Status                                                  │
├──────────────────────┬────────┬──────────┬──────────────────────┤
│ Service              │ Status │ Uptime   │ Last Check           │
├──────────────────────┼────────┼──────────┼──────────────────────┤
│ Backend API          │ ✅ UP  │ 99.97%   │ 18:22:30 (3s ago)    │
│ PostgreSQL           │ ✅ UP  │ 100.00%  │ 18:22:28 (5s ago)    │
│ Redis Cache          │ ✅ UP  │ 99.99%   │ 18:22:30 (3s ago)    │
│ ML Inference Service │ ✅ UP  │ 99.95%   │ 18:22:29 (4s ago)    │
│ Smart Contract RPC   │ ⚠️ SLOW│ 99.82%   │ 18:22:25 (8s ago)    │
│ SIEM Log Collector   │ ✅ UP  │ 100.00%  │ 18:22:31 (2s ago)    │
└──────────────────────┴────────┴──────────┴──────────────────────┘

Resource Usage:
  CPU:    ████████░░░░░░░░░░░░  42% (8 cores)
  Memory: ███████████░░░░░░░░░  58% (16GB / 32GB)
  Disk:   ████░░░░░░░░░░░░░░░░  23% (115GB / 500GB)
  
  ⚠️  Smart Contract RPC latency: 850ms (baseline: 200ms)
  📋 Action: Check Infura/Alchemy status or switch provider
```

---

### Section 6: Security Events (SIEM Feed)

**Layout**: Live event stream with severity filtering

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔒 Security Events (Last 15 Minutes)                           │
│ Filter: [All] [Critical] [High] [Medium] [Low]                 │
├──────────┬──────────┬─────────────────────────────────────────┤
│ Time     │ Severity │ Event                                   │
├──────────┼──────────┼─────────────────────────────────────────┤
│ 18:22:10 │ 🔴 HIGH  │ 5 failed admin login attempts from      │
│          │          │ IP 203.0.113.99 → Account locked        │
├──────────┼──────────┼─────────────────────────────────────────┤
│ 18:20:45 │ 🟡 MED   │ Rate limit exceeded: IP 198.51.100.7    │
│          │          │ blocked for 60 minutes                  │
├──────────┼──────────┼─────────────────────────────────────────┤
│ 18:19:12 │ 🟡 MED   │ Fraud model blocked txn_a7f3 (score:    │
│          │          │ 0.91) - wallet 0x742d35Cc...            │
├──────────┼──────────┼─────────────────────────────────────────┤
│ 18:17:33 │ 🟢 LOW   │ SSL certificate renewal successful      │
│          │          │ (expires: 2026-02-28)                   │
├──────────┼──────────┼─────────────────────────────────────────┤
│ 18:15:08 │ 🟡 MED   │ Feature drift score: 0.12 (threshold:   │
│          │          │ 0.15) - monitoring                      │
└──────────┴──────────┴─────────────────────────────────────────┘
```

---

## Alert Rules Configuration

### Alert Rule 1: Fraud Rate Spike

**Trigger**: Fraud detection rate >3% for 10 consecutive minutes  
**Severity**: HIGH  
**Action**:
- Send PagerDuty alert to on-call engineer
- Auto-enable stricter fraud threshold (0.60 → 0.50)
- Log to SIEM with correlation ID

**Query**:
```sql
SELECT 
  COUNT(CASE WHEN decision = 'BLOCKED' THEN 1 END)::float / COUNT(*) AS fraud_rate
FROM fraud_predictions
WHERE timestamp > NOW() - INTERVAL '10 minutes'
HAVING fraud_rate > 0.03;
```

### Alert Rule 2: API Latency Degradation

**Trigger**: p95 latency >100ms for 5 minutes  
**Severity**: MEDIUM  
**Action**:
- Slack notification to #engineering channel
- Auto-scale backend pods (+2 replicas)
- Capture performance profile for analysis

### Alert Rule 3: Model Drift

**Trigger**: KL divergence >0.15 on any feature  
**Severity**: MEDIUM  
**Action**:
- Email to ML team
- Schedule emergency retraining within 24h
- Switch to ensemble model (XGBoost + Random Forest)

### Alert Rule 4: Unauthorized Admin Access Attempt

**Trigger**: 3 failed MFA attempts within 5 minutes  
**Severity**: CRITICAL  
**Action**:
- Lock admin account immediately
- Send SMS to security team
- Log IP to threat intelligence feed
- Trigger SIEM incident response workflow

---

## Dashboard Code Structure

### Backend API (`monitoring_api.py`)

```python
from flask import Flask, jsonify
from flask_cors import CORS
import redis
import psycopg2

app = Flask(__name__)
CORS(app)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/api/monitoring/kpis', methods=['GET'])
def get_kpis():
    """Real-time KPIs from Redis cache"""
    return jsonify({
        'transactions_per_hour': int(redis_client.get('kpi:txn_per_hour') or 0),
        'fraud_rate': float(redis_client.get('kpi:fraud_rate') or 0),
        'api_latency_p95': float(redis_client.get('kpi:latency_p95') or 0),
        'revenue_per_hour': float(redis_client.get('kpi:revenue_per_hour') or 0)
    })

@app.route('/api/monitoring/fraud_feed', methods=['GET'])
def get_fraud_feed():
    """Last 50 high-risk transactions"""
    conn = psycopg2.connect("dbname=ticketing user=admin")
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, transaction_id, fraud_score, decision, top_feature
        FROM fraud_predictions
        WHERE fraud_score > 0.65
        ORDER BY timestamp DESC
        LIMIT 50
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{
        'time': r[0].isoformat(),
        'txn_id': r[1],
        'score': r[2],
        'decision': r[3],
        'top_feature': r[4]
    } for r in results])
```

### Frontend Dashboard (`monitoring_dashboard.py`)

```python
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import requests

app = dash.Dash(__name__, external_stylesheets=['https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'])

app.layout = html.Div([
    html.H1("NFT Ticketing Monitoring Dashboard", className="text-center my-4"),
    
    # KPI Cards
    html.Div([
        html.Div([
            html.H5("Transactions/Hour"),
            html.H2(id='kpi-transactions', children="--"),
            html.P(id='kpi-transactions-delta', children="--")
        ], className="col-md-3 card p-3"),
        # ... repeat for other KPIs
    ], className="row"),
    
    # Fraud Detection Chart
    dcc.Graph(id='fraud-timeseries'),
    
    # Auto-refresh every 5 seconds
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0)
])

@app.callback(
    Output('kpi-transactions', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_kpis(n):
    data = requests.get('http://localhost:5000/api/monitoring/kpis').json()
    return f"{data['transactions_per_hour']:,}"

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8050)
```

---

## Deployment

**Infrastructure**:
- **Backend API**: Docker container on AWS ECS (2 replicas)
- **Dashboard**: Dash app on AWS Fargate (1 replica)
- **Database**: AWS RDS PostgreSQL (db.t3.medium)
- **Cache**: AWS ElastiCache Redis (cache.t3.micro)

**Access Control**:
- Dashboard URL: `https://monitoring.nft-ticketing.com/admin`
- Auth: OAuth 2.0 + MFA (Google Authenticator)
- IP Whitelist: Corporate VPN range (10.0.0.0/8)

**Monitoring the Monitor**:
- Uptime check: Pingdom (1-minute interval)
- Alert if dashboard down >5 minutes → fallback to Grafana

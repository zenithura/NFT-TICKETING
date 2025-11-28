# Baseline KPI Snapshot
## Sprint 3 - NFT Ticketing Platform

**Measurement Period**: 2025-11-01 to 2025-11-28 (4 weeks)  
**Platform Scale**: 50k–200k daily events  
**Data Source**: Production PostgreSQL + Redis

---

## Primary KPIs

| KPI | Current Value | Target | Status | Trend (4 weeks) |
|-----|---------------|--------|--------|-----------------|
| **Fraud Detection Rate** | 94.2% | ≥95% | 🟡 Near Target | ▲ +2.3% |
| **False Positive Rate** | 1.8% | ≤2% | ✅ On Target | ▼ -0.4% |
| **Ticket Resale Velocity** | 18.5 hours | Track baseline | ℹ️ Baseline | ▼ -3.2 hours |
| **User Engagement Score** | 0.32 | ≥0.35 | 🟡 Near Target | ▲ +0.05 |
| **Platform Revenue/Hour** | $11,240 | Track & optimize | ℹ️ Baseline | ▲ +12% |

### KPI Details

#### 1. Fraud Detection Rate: 94.2%

**Calculation**: (Blocked fraudulent transactions / Total fraud attempts) × 100

**Breakdown**:
- Total fraud attempts detected: 1,247
- Successfully blocked: 1,175
- Missed (false negatives): 72

**Analysis**:
- Current model (XGBoost v1.2.3) performs well but misses sophisticated attacks
- Main gap: New wallet addresses with no history (cold start problem)
- **Action**: Implement ensemble model (XGBoost + Isolation Forest) to improve to 96%+

**Weekly Trend**:
```
Week 1: 91.8%
Week 2: 93.1%
Week 3: 94.7%
Week 4: 95.2% ← Improving
```

---

#### 2. False Positive Rate: 1.8%

**Calculation**: (Legitimate transactions flagged as fraud / Total legitimate transactions) × 100

**Breakdown**:
- Total legitimate transactions: 127,450
- Incorrectly flagged: 2,294
- User friction incidents: 89 (required manual review)

**Analysis**:
- Meets target of <2%
- Most false positives from VIP users with high transaction velocity
- **Action**: Add whitelist for verified high-volume users

**Impact**:
- Estimated revenue loss from abandoned carts: $18,400 (4 weeks)
- Customer support tickets: 89 (avg resolution time: 12 minutes)

---

#### 3. Ticket Resale Velocity: 18.5 hours (median)

**Calculation**: Median time from mint to first secondary sale

**Distribution**:
```
Percentile | Time to Resale
-----------|---------------
10th       | 0.3 hours (scalpers)
25th       | 2.1 hours
50th       | 18.5 hours (baseline)
75th       | 72.3 hours
90th       | 168+ hours (collectors)
```

**Analysis**:
- **Scalpers (10th percentile)**: Resell within 20 minutes
  - 8.2% of all tickets
  - Average markup: 47%
- **Normal users (25th–75th)**: Hold for 2–72 hours
- **Collectors (90th+)**: Hold for weeks

**Action**:
- Flag wallets with <1 hour median resale time for fraud review
- Implement dynamic pricing to capture scalper premium

---

#### 4. User Engagement Score: 0.32

**Calculation**: (Events attended / Events browsed) × (Avg ticket hold time / 168 hours)

**Breakdown**:
- Average events browsed per user: 8.4
- Average events attended: 2.1
- Conversion rate: 25%
- Average ticket hold time: 52 hours

**Segment Analysis**:

| Segment | % of Users | Engagement Score | Lifetime Value |
|---------|------------|------------------|----------------|
| VIP (10+ events) | 3.2% | 0.78 | $1,240 |
| Regular (5–9 events) | 12.1% | 0.52 | $520 |
| Casual (2–4 events) | 31.4% | 0.28 | $180 |
| New (1 event) | 53.3% | 0.12 | $65 |

**Action**:
- Increase engagement via personalized recommendations (collaborative filtering)
- Target: Move 10% of "Casual" users to "Regular" → +$3.4M annual revenue

---

#### 5. Platform Revenue per Hour: $11,240

**Calculation**: (Total ticket sales + platform fees) / Total hours in period

**Breakdown**:
- Total revenue (4 weeks): $7.52M
- Platform fees (2.5%): $188k
- Average hourly revenue: $11,240

**Peak vs. Off-Peak**:
```
Peak hours (18:00–22:00 UTC): $18,450/hour
Off-peak (02:00–06:00 UTC): $3,120/hour
Weekend vs. Weekday: +34% higher on weekends
```

**Top Revenue Events**:
1. Concert - Artist A (Nov 15): $420k
2. Sports - Championship (Nov 22): $380k
3. Festival - Music Fest (Nov 8): $310k

**Action**:
- Optimize pricing during peak hours (MAB experiment)
- Increase marketing spend for off-peak events

---

## Secondary Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Gas Cost Efficiency** | 0.0042 ETH/txn | Average gas used: 185,000 units @ 22.7 gwei |
| **API Response Time (p95)** | 48ms | Target: <50ms ✅ |
| **Model Drift Score** | 0.09 | KL divergence, threshold: 0.15 ✅ |
| **Database Query Time (p95)** | 120ms | Materialized views improve by 80% |
| **Cache Hit Rate** | 87% | Redis cache for hot features |
| **Uptime** | 99.94% | 4 incidents (total downtime: 25 minutes) |

---

## Model Performance Baseline

### XGBoost Fraud Classifier v1.2.3

**Training Data**:
- Date range: 2025-01-01 to 2025-10-31 (10 months)
- Total samples: 480,000 transactions
- Fraud rate: 1.2% (5,760 positive samples)
- Class balancing: SMOTE + scale_pos_weight=82

**Test Set Performance** (20% holdout):

| Metric | Value | 95% CI |
|--------|-------|--------|
| AUC-ROC | 0.947 | [0.932, 0.961] |
| AUC-PR | 0.823 | [0.798, 0.847] |
| Precision @ 90% Recall | 0.78 | [0.74, 0.82] |
| F1 Score | 0.81 | [0.78, 0.84] |
| False Positive Rate | 1.8% | [1.5%, 2.2%] |

**Confusion Matrix** (threshold=0.65):
```
                Predicted
              Fraud  Legit
Actual Fraud   687     93    (Recall: 88.1%)
       Legit   214  11,006  (Specificity: 98.1%)
```

**Feature Importance** (SHAP values):
1. `txn_velocity_1h`: 0.24
2. `price_deviation_ratio`: 0.19
3. `wallet_age_days`: 0.16
4. `geo_velocity_flag`: 0.14
5. `avg_ticket_hold_time`: 0.11

---

## Traffic & Usage Statistics

### Platform Activity (4-week average)

| Metric | Daily Average | Peak Day | Notes |
|--------|---------------|----------|-------|
| **Active Users** | 42,300 | 68,200 (Nov 22) | Unique wallet addresses |
| **Transactions** | 8,450 | 14,100 | Includes purchases + transfers |
| **API Requests** | 1.2M | 2.1M | 87% cache hit rate |
| **Events Listed** | 320 | 450 | New events per day |
| **Tickets Minted** | 7,800 | 13,200 | Primary sales |
| **Tickets Resold** | 650 | 1,100 | Secondary market |

### Geographic Distribution

| Region | % of Users | Avg Transaction Value |
|--------|------------|----------------------|
| North America | 42% | $85 |
| Europe | 31% | $72 |
| Asia | 18% | $58 |
| Other | 9% | $45 |

---

## Security Metrics

### Threat Detection (4 weeks)

| Threat Type | Incidents | Blocked | False Positives | Success Rate |
|-------------|-----------|---------|-----------------|--------------|
| **Fraudulent Transactions** | 1,247 | 1,175 | 214 | 94.2% |
| **Rate Limit Violations** | 8,420 | 8,420 | 0 | 100% |
| **Failed Login Attempts** | 3,210 | 89 accounts locked | 2 | 97.2% |
| **Geo-Velocity Anomalies** | 156 | 142 | 8 | 91.0% |
| **Wallet Blacklist Hits** | 47 | 47 | 0 | 100% |

### Incident Response Times

| Severity | Count | Avg Response Time | Avg Resolution Time |
|----------|-------|-------------------|---------------------|
| Critical | 2 | 4 minutes | 18 minutes |
| High | 12 | 8 minutes | 35 minutes |
| Medium | 89 | 15 minutes | 2.3 hours |
| Low | 234 | N/A | 24 hours |

**Notable Incidents**:
1. **Nov 12**: DDoS attack (50k req/min) → Mitigated via Cloudflare in 6 minutes
2. **Nov 19**: Smart contract gas spike (200 gwei) → User notification, no downtime

---

## Cost Metrics

### Infrastructure Costs (monthly)

| Service | Cost | Notes |
|---------|------|-------|
| AWS RDS (PostgreSQL) | $420 | db.r5.xlarge |
| AWS ElastiCache (Redis) | $180 | cache.r5.large |
| AWS ECS (Containers) | $650 | 8 tasks, Fargate |
| Infura/Alchemy (Web3) | $250 | 2M requests/month |
| CloudFlare (CDN + WAF) | $200 | Pro plan |
| Monitoring (Datadog) | $150 | 10 hosts |
| **Total** | **$1,850** | **$0.022 per transaction** |

**Cost Optimization Opportunities**:
- Move to Aurora Serverless: -$120/month
- Implement query caching: -30% RDS load
- Optimize container scaling: -$150/month

---

## Data Quality Metrics

### ETL Pipeline Health

| Check | Pass Rate | Issues (4 weeks) |
|-------|-----------|------------------|
| **Schema Validation** | 99.98% | 12 malformed events |
| **Null Value Check** | 100% | 0 critical nulls |
| **Duplicate Detection** | 99.95% | 34 duplicates removed |
| **Data Freshness** | 99.92% | 5 delays >1 hour |
| **Volume Anomaly** | 100% | 0 unexpected drops |

### Feature Quality

| Feature | Null Rate | Outlier Rate | Drift Score |
|---------|-----------|--------------|-------------|
| `txn_velocity_1h` | 0% | 0.8% | 0.04 |
| `wallet_age_days` | 0% | 0% | 0.02 |
| `price_deviation_ratio` | 2.1% | 3.2% | 0.11 |
| `event_popularity_score` | 0.3% | 1.1% | 0.07 |

---

## Recommendations Based on Baseline

### Immediate Actions (Sprint 4)

1. **Improve Fraud Detection to 96%+**
   - Deploy ensemble model (XGBoost + Isolation Forest)
   - Add whitelist for VIP users to reduce false positives

2. **Increase User Engagement to 0.35+**
   - Launch recommender system (collaborative filtering)
   - Personalized email campaigns for "Casual" segment

3. **Optimize Revenue per Hour**
   - Deploy MAB pricing experiment (4 arms)
   - Target 5% revenue increase → +$562/hour

### Long-Term Optimizations

1. **Cost Reduction**: Migrate to serverless architecture (-20% infra costs)
2. **Scalability**: Implement horizontal sharding for PostgreSQL (support 1M+ daily events)
3. **Advanced ML**: Add LSTM for demand forecasting, graph neural networks for fraud rings

---

## Data Export

**Full Dataset**: Available in `/data/baseline_kpis_2025_11_28.csv`

**Sample Query** (PostgreSQL):
```sql
SELECT 
    DATE_TRUNC('day', timestamp) AS date,
    COUNT(*) AS transactions,
    SUM(price_paid) AS revenue,
    AVG(fraud_score) AS avg_fraud_score
FROM transactions
JOIN fraud_predictions USING (transaction_id)
WHERE timestamp BETWEEN '2025-11-01' AND '2025-11-28'
GROUP BY date
ORDER BY date;
```

---

**Report Generated**: 2025-11-28 18:22:33 UTC  
**Next Review**: 2025-12-28 (monthly cadence)

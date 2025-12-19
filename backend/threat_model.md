# Threat Model: NFT Ticketing Platform

This document identifies the top security and operational risks for the NFT Ticketing Platform and outlines mitigation strategies.

## Risk Matrix

| Risk ID | Threat | Likelihood | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | **Event Lag / Stale UI** | High | Medium | Real-time monitoring of lag with alerts; automated cache invalidation. | DevOps |
| T2 | **Fake Event Injection** | Medium | High | Cryptographic verification of event signatures; admin-only event creation with 2FA. | Security |
| T3 | **Unauthorized Admin Access** | Low | Critical | Basic Auth + IP Whitelisting; Role-Based Access Control (RBAC); Audit logging. | Security |
| T4 | **Rate Limit Bypass** | Medium | Medium | Multi-layer rate limiting (API Gateway + Middleware); Redis-backed counters. | Backend |
| T5 | **Data Leakage (PII)** | Low | High | Data retention policy (auto-deletion); encryption at rest; minimal data collection. | Compliance |

## Detailed Threat Analysis

### T1: Event Lag Leading to Stale UI
- **Description**: The indexer falls behind the blockchain, causing users to see tickets that are already sold.
- **Mitigation**: 
    - Implemented `event_processing_lag` KPI in `monitoring/monitoring_api.py`.
    - Alert triggers if lag > 60s (`monitoring/alert_rules.py`).
    - UI displays "Syncing..." status when lag is detected.

### T2: Injection of Fake Events
- **Description**: An attacker bypasses the API to inject fraudulent events into the database.
- **Mitigation**:
    - All event creation endpoints require `admin_secret` or valid JWT.
    - Database constraints prevent duplicate or malformed event IDs.
    - SIEM monitoring for unusual spikes in event creation.

### T3: Unauthorized Admin Access
- **Description**: An attacker gains access to the admin dashboard to manipulate prices or drain funds.
- **Mitigation**:
    - Admin dashboard protected by `Basic Auth` (Sprint 3 requirement).
    - All admin actions logged to `audit_logs` table.
    - Session timeouts and secure cookie flags.

### T4: Rate Limit Bypass
- **Description**: Bots overwhelm the API to scrape data or perform scalping.
- **Mitigation**:
    - `RateLimitMiddleware` implemented in `backend/middleware/security.py`.
    - Monitoring of `rate_limit_exceeded` events on the dashboard.
    - Dynamic blacklisting of IPs showing bot-like behavior (SOAR).

### T5: Data Leakage
- **Description**: Sensitive user data or transaction history is exposed.
- **Mitigation**:
    - `DataRetentionPolicy` in `data_control/data_retention.py` archives data after 90 days.
    - Off-chain data minimized; only essential hashes stored on-chain.

## Monitoring & Response
- **KPIs**: Lag, Error Rate, Suspicious TX Count, API Latency.
- **Alerts**: Automated alerts via `AlertSystem`.
- **SOAR**: Automated blocking of malicious IPs (to be implemented in `soar_engine.py`).

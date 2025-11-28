# Threat Model One-Pager
## NFT Ticketing Platform Security Assessment

**Assessment Date**: 2025-11-28  
**Platform**: NFT Ticketing (50k–200k daily events)  
**Scope**: Smart contracts, backend API, ML models, user data

---

## Top 5 Security Risks

| # | Threat | Attack Vector | Likelihood | Impact | Risk Score |
|---|--------|---------------|------------|--------|------------|
| **1** | **Smart Contract Reentrancy** | Malicious contract calls `buyTicket()` recursively before state update | Medium | High | **HIGH** |
| **2** | **API Rate Limit Bypass** | Distributed botnet rotates IPs to scrape ticket inventory | High | Medium | **HIGH** |
| **3** | **ML Model Poisoning** | Attacker submits crafted transactions to skew fraud model training | Low | High | **MEDIUM** |
| **4** | **Admin Dashboard Auth Bypass** | Credential stuffing or session hijacking on `/admin` routes | Medium | High | **HIGH** |
| **5** | **Data Exfiltration via Logs** | Sensitive PII leaked in application logs or monitoring dashboards | Medium | Medium | **MEDIUM** |

---

## Likelihood × Impact Matrix

```
         Impact →
    │  Low    Medium   High
────┼─────────────────────────
Low │         T3
    │
Med │  T5     T5       T2, T4
    │
High│         T2
```

**Legend**: T1=Reentrancy, T2=Rate Limit, T3=Model Poison, T4=Auth Bypass, T5=Data Leak

---

## Detailed Threat Analysis & Mitigations

### Threat 1: Smart Contract Reentrancy Attack

**Description**: Attacker deploys malicious contract that calls `buyTicket()` and re-enters before `ticketsSold` counter updates, minting multiple tickets while paying once.

**Likelihood**: Medium (requires technical sophistication, but well-known attack)  
**Impact**: High (financial loss, event overselling, reputation damage)

**Mitigations**:
- ✅ **Checks-Effects-Interactions Pattern**: Update state before external calls
- ✅ **ReentrancyGuard**: Use OpenZeppelin's `nonReentrant` modifier on all payable functions
- ✅ **Gas Limit**: Limit gas forwarded to external calls (<2300 gas)
- 🔄 **Audit**: Third-party security audit before mainnet deployment

**Code Example**:
```solidity
function buyTicket(uint256 eventId) external payable nonReentrant {
    require(events[eventId].ticketsSold < events[eventId].capacity, "Sold out");
    events[eventId].ticketsSold++;  // State update BEFORE external call
    _mint(msg.sender, ticketId);
    emit TicketPurchased(msg.sender, eventId, ticketId);
}
```

---

### Threat 2: API Rate Limit Bypass

**Description**: Botnet with 10k+ IPs floods `/api/events` endpoint to scrape real-time inventory, enabling scalpers to auto-purchase high-demand tickets.

**Likelihood**: High (common attack, low barrier to entry)  
**Impact**: Medium (degrades service, enables scalping, increases costs)

**Mitigations**:
- ✅ **Multi-Layer Rate Limiting**:
  - IP-based: 100 req/min per IP (Redis sliding window)
  - User-based: 500 req/min per authenticated user
  - Endpoint-specific: `/buy` limited to 5 req/min
- ✅ **CAPTCHA**: Require on suspicious activity (velocity spike, new IP)
- ✅ **WAF Rules**: Block known bot user-agents, Tor exit nodes
- ✅ **Adaptive Throttling**: Reduce limits during detected DDoS (auto-scale down)

**Implementation**:
```python
# Middleware: flask_limiter
@limiter.limit("100 per minute", key_func=get_remote_address)
@limiter.limit("500 per minute", key_func=get_user_id)
def get_events():
    # ...
```

---

### Threat 3: ML Model Poisoning

**Description**: Attacker creates 1000 fake accounts, executes legitimate-looking transactions to poison training data, causing model to whitelist future fraud.

**Likelihood**: Low (requires sustained effort, domain knowledge)  
**Impact**: High (model becomes ineffective, fraud spike)

**Mitigations**:
- ✅ **Data Validation**: Reject outliers beyond 99th percentile during ingestion
- ✅ **Anomaly Detection on Training Data**: Flag sudden distribution shifts
- ✅ **Human Labeling**: Manual review of fraud labels before retraining
- ✅ **Model Versioning**: Rollback capability if performance degrades
- 🔄 **Adversarial Training**: Augment dataset with synthetic attack patterns

**Monitoring**:
- Alert if fraud rate changes >20% week-over-week
- Track feature drift score (KL divergence) – threshold: 0.15

---

### Threat 4: Admin Dashboard Authentication Bypass

**Description**: Attacker uses credential stuffing (leaked passwords from other breaches) or steals session token to access `/admin/metrics` dashboard with sensitive data.

**Likelihood**: Medium (common attack, depends on password hygiene)  
**Impact**: High (full system visibility, potential data manipulation)

**Mitigations**:
- ✅ **Multi-Factor Authentication (MFA)**: Enforce TOTP for all admin accounts
- ✅ **IP Whitelisting**: Restrict `/admin/*` routes to corporate VPN IPs
- ✅ **Session Security**:
  - HTTPOnly, Secure, SameSite=Strict cookies
  - 15-minute session timeout
  - Rotate session ID on privilege escalation
- ✅ **Audit Logging**: Log all admin actions with IP, timestamp, user
- ✅ **Rate Limiting**: 5 failed login attempts → 1-hour lockout

**Tech Stack**:
- Auth: Flask-Login + pyotp (TOTP)
- Session: Redis-backed with 900s TTL
- Audit: PostgreSQL `admin_audit_log` table

---

### Threat 5: Data Exfiltration via Logs

**Description**: Application logs contain user emails, wallet addresses, or transaction details. Logs stored in plaintext on disk or sent to third-party monitoring (Datadog, Sentry).

**Likelihood**: Medium (common misconfiguration)  
**Impact**: Medium (GDPR violation, user privacy breach)

**Mitigations**:
- ✅ **PII Redaction**: Scrub emails, IPs, wallet addresses from logs
  ```python
  import re
  def redact_pii(message):
      message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', message)
      message = re.sub(r'0x[a-fA-F0-9]{40}', '0x[REDACTED]', message)
      return message
  ```
- ✅ **Structured Logging**: Use JSON format, separate PII into encrypted fields
- ✅ **Log Retention**: 30-day rolling window, encrypted at rest (AES-256)
- ✅ **Access Control**: Logs accessible only to DevOps team (RBAC)
- 🔄 **DLP Scanning**: Automated scan for accidental PII leakage

---

## Additional Security Controls

### Defense in Depth

| Layer | Control | Status |
|-------|---------|--------|
| **Network** | CloudFlare DDoS protection, WAF | ✅ Implemented |
| **Application** | Input validation, parameterized queries | ✅ Implemented |
| **Data** | Encryption at rest (PostgreSQL TDE), in transit (TLS 1.3) | ✅ Implemented |
| **Identity** | OAuth 2.0 + JWT, MFA for admins | ✅ Implemented |
| **Monitoring** | SIEM alerts, anomaly detection | 🔄 Sprint 3 |

### Incident Response Plan

1. **Detection**: SIEM alert triggers (e.g., fraud spike, failed auth surge)
2. **Triage**: On-call engineer assesses severity (P0–P3)
3. **Containment**: Rate limit aggressive IPs, disable compromised accounts
4. **Eradication**: Patch vulnerability, rotate secrets
5. **Recovery**: Restore from backup if needed, re-enable services
6. **Post-Mortem**: Document root cause, update runbooks

**Escalation Path**: Engineer → Team Lead → CISO (for P0/P1)

---

## Compliance & Regulatory

- **GDPR**: Right to erasure implemented (delete user data on request)
- **PCI-DSS**: Not applicable (crypto payments only, no card data)
- **SOC 2 Type II**: Planned for Q2 2026
- **Bug Bounty**: HackerOne program launch in Sprint 5 ($500–$5000 rewards)

---

## Risk Acceptance

The following risks are **accepted** (low likelihood × low impact):
- **Threat**: Frontend XSS via user-generated event descriptions  
  **Rationale**: Markdown sanitized with DOMPurify, CSP headers enforced  
  **Residual Risk**: Low

- **Threat**: Blockchain network congestion (gas price spike)  
  **Rationale**: Users informed of gas costs before transaction  
  **Residual Risk**: Low (business continuity, not security)

---

## Review & Updates

**Next Review**: 2025-12-28 (monthly cadence)  
**Owner**: Security Team + DevOps Lead  
**Distribution**: Engineering, Product, Executive team

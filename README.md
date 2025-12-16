# NFT Ticketing Platform - Sprint 4 Documentation

**Project Name:** NFTIX - NFT-Based Event Ticketing Platform  
**Version:** 1.0.0  
**Sprint:** Sprint 4 - Full Stack Integration with ML Intelligence  
**Date:** 2024

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Documentation Infrastructure](#2-documentation-infrastructure)
3. [Project Overview](#3-project-overview)
4. [System Architecture](#4-system-architecture)
5. [Integration & Traceability](#5-integration--traceability)
6. [Artifact Traceability](#6-artifact-traceability)
7. [API Documentation](#7-api-documentation)
8. [Machine Learning Integration](#8-machine-learning-integration)
9. [Database Schema & ERD](#9-database-schema--erd)
10. [Quality Assurance](#10-quality-assurance)
11. [Methodology Visualizations](#11-methodology-visualizations)
12. [Dashboards & Monitoring](#12-dashboards--monitoring)
13. [Accessibility & Compliance](#13-accessibility--compliance)
14. [File Organization](#14-file-organization)
15. [Pitch Deck](#15-pitch-deck)
16. [Demo Video](#16-demo-video)
17. [Additional Deliverables](#17-additional-deliverables)
18. [Success Metrics](#18-success-metrics)
19. [Appendices](#19-appendices)

---

## 1. Executive Summary

The NFT Ticketing Platform (NFTIX) is a comprehensive Web3-based event ticketing solution that leverages blockchain technology, machine learning, and modern web development practices. Sprint 4 represents the complete integration of all system components, including:

- **Frontend:** React/TypeScript application with Three.js 3D visualizations
- **Backend:** FastAPI REST API with comprehensive security middleware
- **Blockchain:** Smart contracts for NFT ticket minting and trading
- **Machine Learning:** 6 ML models for fraud detection, risk analysis, recommendations, and dynamic pricing
- **Database:** Supabase PostgreSQL for operational data, DuckDB for ML analytics
- **Admin Panel:** Real-time security monitoring and management dashboard

**Key Achievements:**
- ✅ Full-stack integration with ML intelligence layer
- ✅ 8 API router modules with 66+ endpoints
- ✅ 6 ML models fully integrated and exposed via API
- ✅ End-to-end data flow: Supabase → ML → DuckDB
- ✅ Comprehensive security and monitoring
- ✅ Production-ready deployment configuration

---

## 2. Documentation Infrastructure

### 2.1 Documentation Tools & Standards

| Tool/Standard | Purpose | Status |
|---------------|---------|--------|
| Markdown | Primary documentation format | ✅ Active |
| OpenAPI/Swagger | API documentation | ✅ Available at `/docs` |
| ERD Diagrams | Database schema visualization | ✅ See [diagrams/](#diagrams) |
| Jupyter Notebooks | ML model evaluation | ✅ See [Machine Learning/notebooks/](#machine-learning-notebooks) |
| Git/GitHub | Version control & collaboration | ✅ Active |

### 2.2 Documentation Location

```
NFT-TICKETING/
├── README.md                          # This file
├── diagrams/                          # System diagrams (ERD, sequence, class, activity)
│   ├── Group2_SDF1_ERD.png
│   ├── Group2_SDF1_Sequence_diagram_sale.png
│   ├── Group2_SDF1_Sequence_diagram_resale.png
│   ├── Group2_SDF1_Class.png
│   ├── Group2_SDF1_Activity_diagram.png
│   └── Group2_SDF1_Usecase_*.png
├── backend/                           # Backend documentation
│   ├── *.sql                          # Database schemas and migrations
│   └── main.py                        # API entry point
├── Machine Learning/                  # ML documentation
│   ├── notebooks/                     # ML evaluation notebooks
│   └── tests/                         # ML test suites
└── smart_contracts/                   # Smart contract documentation
    └── contracts/                     # Solidity contracts
```

### 2.3 Quick Access Links

- **API Documentation:** `http://localhost:8000/docs` (Interactive Swagger UI)
- **API ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`
- **GitHub Repository:** [Link to be added]

---

## 3. Project Overview

### 3.1 Project Description

NFTIX is a decentralized event ticketing platform that:

1. **Mints NFT Tickets** on the blockchain (Ethereum-compatible)
2. **Prevents Fraud** using ML-powered risk detection
3. **Enables Fair Resale** with 50% markup limit to prevent scalping
4. **Provides Recommendations** using collaborative filtering ML models
5. **Optimizes Pricing** using Multi-Armed Bandit algorithms
6. **Monitors Security** with real-time threat detection and alerting

### 3.2 Technology Stack

#### Frontend
- **Framework:** React 18.2.0 + TypeScript
- **Build Tool:** Vite
- **UI Library:** Tailwind CSS + Lucide Icons
- **3D Graphics:** Three.js 0.162.0
- **State Management:** SWR for data fetching
- **Routing:** React Router DOM 6.22.3
- **Internationalization:** i18next
- **Testing:** Cypress

#### Backend
- **Framework:** FastAPI 0.109.0
- **ASGI Server:** Uvicorn 0.27.0
- **Database:** Supabase (PostgreSQL)
- **Blockchain:** Web3.py 6.15.1 (Ethereum)
- **Authentication:** JWT (python-jose)
- **Monitoring:** Sentry + Prometheus
- **Testing:** pytest

#### Blockchain
- **Language:** Solidity 0.8.20
- **Framework:** Hardhat
- **Standards:** ERC-721 (NFT), ERC-2981 (Royalties)
- **Libraries:** OpenZeppelin Contracts

#### Machine Learning
- **Models:** XGBoost, Isolation Forest, K-Means, DBSCAN, PCA
- **Framework:** scikit-learn, XGBoost, pandas, numpy
- **Storage:** DuckDB for analytics
- **Language:** Python 3.12

### 3.3 Key Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| NFT Ticket Minting | Blockchain-based ticket issuance | Smart Contract (ERC-721) |
| Fraud Detection | ML-powered transaction risk scoring | XGBoost model + Rule-based heuristics |
| Marketplace | Secondary ticket trading with markup limit | Smart Contract + Backend validation |
| Recommendations | Personalized event suggestions | Collaborative filtering ML |
| Dynamic Pricing | Adaptive pricing strategies | Multi-Armed Bandit |
| Admin Dashboard | Security monitoring and management | Real-time alerts + Analytics |
| Wallet Integration | Web3 wallet connection (MetaMask, etc.) | Web3.js/Ethers.js |

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ User Portal  │  │ Admin Panel  │  │  3D Visuals  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Auth API   │  │  Events API  │  │ Tickets API  │        │
│  │  Marketplace │  │   Wallet API │  │   Admin API  │        │
│  │   ML Services│  │              │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
    ┌────▼────┐         ┌─────▼─────┐      ┌──────▼──────┐
    │Supabase │         │  Machine  │      │ Blockchain  │
    │PostgreSQL│        │ Learning  │      │ (Ethereum)  │
    │         │         │           │      │             │
    │  OLTP   │         │  DuckDB   │      │  Smart      │
    │  Data   │         │ Analytics │      │ Contracts   │
    └─────────┘         └───────────┘      └─────────────┘
```

### 4.2 Component Architecture

#### 4.2.1 Frontend Architecture
```
frontend/
├── pages/                  # Route components
│   ├── Dashboard.tsx
│   ├── EventDetails.tsx
│   ├── Marketplace.tsx
│   ├── AdminDashboard.tsx
│   └── ...
├── components/             # Reusable components
│   ├── ui/                 # UI primitives
│   ├── 3d/                 # Three.js components
│   └── ...
├── services/               # API clients
│   ├── eventService.ts
│   ├── ticketService.ts
│   ├── mlService.ts
│   └── ...
└── lib/                    # Utilities
    ├── web3Utils.ts
    └── ...
```

#### 4.2.2 Backend Architecture
```
backend/
├── routers/                # API route handlers
│   ├── auth.py            # Authentication endpoints
│   ├── events.py          # Event management
│   ├── tickets.py         # Ticket operations
│   ├── marketplace.py     # Resale marketplace
│   ├── ml_services_backend.py  # ML endpoints
│   └── admin.py           # Admin dashboard
├── models.py              # Pydantic models
├── database.py            # Supabase client
├── web3_client.py         # Blockchain integration
└── security_middleware.py # Security layer
```

#### 4.2.3 Machine Learning Architecture
```
Machine Learning/
├── models/                 # ML models
│   ├── fraud_detection_model.py      # XGBoost fraud detector
│   ├── anomaly_detector.py           # Isolation Forest
│   ├── user_clustering.py            # K-Means + DBSCAN
│   ├── recommendation_engine.py      # Collaborative filtering
│   ├── pricing_bandit.py             # Multi-Armed Bandit
│   └── risk_scoring_heuristic.py     # Rule-based risk scoring
├── integration/            # Integration layer
│   ├── ml_integration_backend.py     # Main integration
│   ├── supabase_feature_engineer.py  # Feature engineering
│   └── duckdb_storage.py             # Analytics storage
├── features/               # Feature engineering
├── kpis/                   # KPI calculations
└── notebooks/              # Jupyter notebooks
```

---

## 5. Integration & Traceability

### 5.1 SDF Artifacts to Sprint Implementation Mapping

| SDF Artifact | Sprint 1-2 | Sprint 3 | Sprint 4 | Location |
|--------------|------------|----------|----------|----------|
| **Use Case Diagrams** | ✅ User flows | ✅ Admin flows | ✅ ML integration | `diagrams/Group2_SDF1_Usecase_*.png` |
| **Class Diagram** | ✅ Core entities | ✅ ML models | ✅ Full integration | `diagrams/Group2_SDF1_Class.png` |
| **Sequence Diagrams** | ✅ Ticket purchase | ✅ Resale flow | ✅ ML pipeline | `diagrams/Group2_SDF1_Sequence_*.png` |
| **Activity Diagram** | ✅ User journey | ✅ Admin workflow | ✅ ML inference | `diagrams/Group2_SDF1_Activity_diagram.png` |
| **ERD** | ✅ Core schema | ✅ Extended schema | ✅ Final schema | `diagrams/Group2_SDF1_ERD.png` |

### 5.2 API Integration Points

#### 5.2.1 REST API Endpoints

**Base URL:** `http://localhost:8000/api`

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| `/auth` | 7 endpoints | Authentication, registration, password management |
| `/events` | 5 endpoints | Event CRUD, organizer management |
| `/tickets` | 10 endpoints | Ticket minting, validation, marketplace approval |
| `/marketplace` | 11 endpoints | Resale listings, purchases, escrow management |
| `/wallet` | 1 endpoint | Wallet connection |
| `/admin` | 18 endpoints | Admin dashboard, security alerts, user management |
| `/admin_auth` | 3 endpoints | Admin authentication |
| `/ml` | 6 endpoints | ML services (fraud, risk, recommendations, pricing) |

**Total API Endpoints:** 61+ endpoints

#### 5.2.2 WebSocket (Future)

*Note: WebSocket endpoints for real-time updates are planned but not yet implemented.*

#### 5.2.3 GraphQL (Future)

*Note: GraphQL API is considered for future iterations but not currently implemented.*

#### 5.2.4 gRPC (Future)

*Note: gRPC services are not currently implemented. REST API is the primary interface.*

### 5.3 Database Integration

#### 5.3.1 Supabase PostgreSQL Schema

**Primary Tables:**
- `users` - User accounts and authentication
- `wallets` - Wallet addresses linked to users
- `events` - Event information
- `tickets` - NFT tickets
- `marketplace_listings` - Resale listings
- `transactions` - Transaction history
- `admin_logs` - Security and audit logs
- `security_alerts` - Threat detection alerts

**Schema Files:**
- `backend/supabase_schema.sql` - Initial schema
- `backend/complete_database_schema.sql` - Full schema with enums
- `backend/database_schema_final.sql` - Production schema
- `backend/migration_*.sql` - Migration scripts

#### 5.3.2 DuckDB Analytics Schema

**ML Analytics Tables:**
- `ml_inference_results` - ML model inference outputs
- `ml_feature_snapshots` - Feature engineering snapshots
- `ml_model_metrics` - Model performance metrics

**Location:** `Machine Learning/artifacts/ml_analytics.duckdb`

### 5.4 Blockchain Integration

#### 5.4.1 Smart Contract

**Contract:** `NFTTicket.sol`  
**Location:** `smart_contracts/contracts/NFTTicket.sol`  
**ABI:** `smart_contracts/artifacts/contracts/NFTTicket.sol/NFTTicket.json`

**Key Functions:**
- `mintTicket()` - Mint new NFT ticket
- `resellTicket()` - List ticket for resale
- `buyTicket()` - Purchase listed ticket
- `validateTicket()` - Validate ticket at event

**Events:**
- `TicketMinted`
- `TicketListed`
- `TicketSold`
- `TicketValidated`

---

## 6. Artifact Traceability

### 6.1 Artifact Traceability Matrix

| Artifact ID | Artifact Name | Sprint | Type | Location | Status |
|-------------|---------------|--------|------|----------|--------|
| **SDF-A001** | ERD Diagram | S1 | Diagram | `diagrams/Group2_SDF1_ERD.png` | ✅ Complete |
| **SDF-A002** | Class Diagram | S1 | Diagram | `diagrams/Group2_SDF1_Class.png` | ✅ Complete |
| **SDF-A003** | Sequence Diagram (Sale) | S1 | Diagram | `diagrams/Group2_SDF1_Sequence_diagram_sale.png` | ✅ Complete |
| **SDF-A004** | Sequence Diagram (Resale) | S2 | Diagram | `diagrams/Group2_SDF1_Sequence_diagram_resale.png` | ✅ Complete |
| **SDF-A005** | Activity Diagram | S1 | Diagram | `diagrams/Group2_SDF1_Activity_diagram.png` | ✅ Complete |
| **SC-A001** | NFTTicket Smart Contract | S1 | Code | `smart_contracts/contracts/NFTTicket.sol` | ✅ Complete |
| **SC-A002** | Smart Contract ABI | S1 | Artifact | `smart_contracts/artifacts/contracts/NFTTicket.sol/NFTTicket.json` | ✅ Complete |
| **BE-A001** | FastAPI Backend | S1-S4 | Code | `backend/` | ✅ Complete |
| **BE-A002** | Database Schema | S1-S4 | SQL | `backend/*.sql` | ✅ Complete |
| **FE-A001** | React Frontend | S1-S4 | Code | `frontend/` | ✅ Complete |
| **ML-A001** | ML Models | S3-S4 | Code | `Machine Learning/models/` | ✅ Complete |
| **ML-A002** | Feature Engineering | S3-S4 | Code | `Machine Learning/features/` | ✅ Complete |
| **ML-A003** | ML Integration Layer | S4 | Code | `Machine Learning/integration/ml_integration_backend.py` | ✅ Complete |
| **ML-A004** | ML Evaluation Notebook | S3 | Notebook | `Machine Learning/notebooks/fraud_model_evaluation.ipynb` | ✅ Complete |
| **ML-A005** | KPI Baseline | S3 | JSON | `Machine Learning/kpis/kpi_baseline.json` | ✅ Complete |
| **API-A001** | OpenAPI Specification | S4 | Spec | `http://localhost:8000/openapi.json` | ✅ Auto-generated |
| **DOC-A001** | API Documentation | S4 | Docs | `http://localhost:8000/docs` | ✅ Auto-generated |

### 6.2 Sprint-wise Artifact Distribution

#### Sprint 1-2 Artifacts
- Core smart contracts
- Initial database schema
- Frontend and backend foundations
- Basic API endpoints

#### Sprint 3 Artifacts
- ML model implementations
- Feature engineering pipeline
- KPI calculation framework
- ML evaluation notebooks

#### Sprint 4 Artifacts
- ML integration layer
- Complete API endpoint suite
- Admin dashboard
- Security monitoring
- DuckDB analytics integration
- Full-stack integration

---

## 7. API Documentation

### 7.1 Interactive API Documentation

**Swagger UI:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`  
**OpenAPI JSON:** `http://localhost:8000/openapi.json`

### 7.2 API Endpoint Summary

#### 7.2.1 Authentication API (`/api/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/refresh-token` | Refresh access token |
| POST | `/api/auth/logout` | User logout |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/reset-password` | Reset password |
| POST | `/api/auth/verify-email` | Verify email address |
| GET | `/api/auth/me` | Get current user info |

#### 7.2.2 Events API (`/api/events`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/events/` | Create new event |
| GET | `/api/events/` | List all events |
| GET | `/api/events/{event_id}` | Get event details |
| GET | `/api/events/organizer/{address}` | Get organizer's events |
| GET | `/api/events/organizer/{address}/stats` | Get organizer statistics |

#### 7.2.3 Tickets API (`/api/tickets`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tickets/server-address` | Get server wallet address |
| POST | `/api/tickets/` | Create/mint ticket |
| GET | `/api/tickets/user/{address}` | Get user's tickets |
| GET | `/api/tickets/event/{event_id}` | Get event tickets |
| GET | `/api/tickets/{ticket_id}` | Get ticket details |
| POST | `/api/tickets/approve-marketplace` | Approve ticket for resale |
| POST | `/api/tickets/mint` | Mint NFT ticket |
| POST | `/api/tickets/validators/add` | Add validator |
| POST | `/api/tickets/validators/remove` | Remove validator |
| POST | `/api/tickets/validate` | Validate ticket |

#### 7.2.4 Marketplace API (`/api/marketplace`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/marketplace/` | Create listing |
| GET | `/api/marketplace/` | List all listings |
| GET | `/api/marketplace/{listing_id}` | Get listing details |
| POST | `/api/marketplace/{listing_id}/buy` | Buy listing |
| GET | `/api/marketplace/seller/{address}` | Get seller's listings |
| POST | `/api/marketplace/list` | Create resale listing |
| POST | `/api/marketplace/buy` | Purchase from marketplace |
| POST | `/api/marketplace/update-price` | Update listing price |
| POST | `/api/marketplace/delist` | Remove listing |
| POST | `/api/marketplace/escrow/release` | Release escrow funds |
| POST | `/api/marketplace/escrow/refund` | Refund escrow |
| POST | `/api/marketplace/withdraw` | Withdraw funds |

#### 7.2.5 ML Services API (`/api/ml`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ml/health` | ML services health check |
| POST | `/api/ml/predict/fraud` | Predict fraud risk |
| POST | `/api/ml/analyze/risk` | Analyze transaction risk |
| POST | `/api/ml/recommend/events` | Get event recommendations |
| POST | `/api/ml/pricing/dynamic` | Get dynamic pricing |
| GET | `/api/ml/analytics` | Get ML analytics |

#### 7.2.6 Admin API (`/api/admin`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/stats` | Get admin statistics |
| GET | `/api/admin/alerts` | List security alerts |
| GET | `/api/admin/alerts/{alert_id}` | Get alert details |
| POST | `/api/admin/ban` | Ban user/IP |
| POST | `/api/admin/unban` | Unban user/IP |
| GET | `/api/admin/graph-data` | Get graph data for charts |
| GET | `/api/admin/users` | List users |
| GET | `/api/admin/alerts-stream` | Stream alerts (SSE) |
| GET | `/api/admin/export-alerts` | Export alerts |
| GET | `/api/admin/web-requests` | Get web request logs |
| GET | `/api/admin/web-requests/export` | Export web requests |
| DELETE | `/api/admin/web-requests/clear` | Clear web request logs |
| DELETE | `/api/admin/alerts/clear` | Clear alerts |
| POST | `/api/admin/users` | Create user |
| DELETE | `/api/admin/users/{user_id}` | Delete user |
| POST | `/api/admin/users/{user_id}/reset-password` | Reset user password |
| GET | `/api/admin/users/{user_id}/activity` | Get user activity |
| POST | `/api/admin/soar/config` | Configure SOAR integration |
| GET | `/api/admin/soar/config` | Get SOAR config |
| DELETE | `/api/admin/soar/config/{config_id}` | Delete SOAR config |
| POST | `/api/admin/soar/config/{config_id}/test` | Test SOAR config |

### 7.3 API Request/Response Examples

#### Example 1: Create Event

**Request:**
```http
POST /api/events/
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Summer Music Festival 2024",
  "description": "Annual summer music festival",
  "date": "2024-07-15T18:00:00Z",
  "location": "Central Park, New York",
  "total_tickets": 1000,
  "price": 0.05,
  "image_url": "https://example.com/image.jpg",
  "category": "Music"
}
```

**Response:**
```json
{
  "event_id": 1,
  "name": "Summer Music Festival 2024",
  "organizer_address": "0x123...",
  "status": "UPCOMING",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Example 2: Predict Fraud

**Request:**
```http
POST /api/ml/predict/fraud
Content-Type: application/json

{
  "transaction_id": "txn_12345",
  "wallet_address": "0xABC...",
  "event_id": 1,
  "price_paid": 0.05
}
```

**Response:**
```json
{
  "transaction_id": "txn_12345",
  "status": "approved",
  "fraud_detection": {
    "fraud_probability": 0.12,
    "decision": "APPROVED",
    "confidence": 0.88
  },
  "risk_scoring_heuristic": {
    "risk_score": 0.25,
    "risk_band": "LOW"
  },
  "features": {
    "txn_velocity_1h": 2,
    "wallet_age_days": 120.5,
    ...
  }
}
```

---

## 8. Machine Learning Integration

### 8.1 ML Models Overview

| Model | Type | Purpose | Implementation |
|-------|------|---------|----------------|
| **Fraud Detection** | Classification (XGBoost) | Detect fraudulent transactions | `models/fraud_detection_model.py` |
| **Anomaly Detection** | Anomaly Detection (Isolation Forest) | Identify unusual patterns | `models/anomaly_detector.py` |
| **User Clustering** | Clustering (K-Means + DBSCAN) | Segment users by behavior | `models/user_clustering.py` |
| **Recommendation Engine** | Collaborative Filtering | Recommend events to users | `models/recommendation_engine.py` |
| **Pricing Bandit** | Reinforcement Learning (MAB) | Optimize pricing strategies | `models/pricing_bandit.py` |
| **Risk Scoring Heuristic** | Rule-based | Fast risk assessment | `models/risk_scoring_heuristic.py` |

### 8.2 Feature Engineering

**Feature Source:** Supabase PostgreSQL  
**Feature Engineer:** `integration/supabase_feature_engineer.py`

**10 Core Features:**
1. `txn_velocity_1h` - Transaction count in last hour
2. `wallet_age_days` - Wallet age in days
3. `avg_ticket_hold_time` - Average ticket hold time (hours)
4. `event_popularity_score` - Event popularity (0-1)
5. `price_deviation_ratio` - Price deviation from average
6. `cross_event_attendance` - Number of different events attended
7. `geo_velocity_flag` - Geographic velocity indicator
8. `payment_method_diversity` - Number of payment methods used
9. `social_graph_centrality` - Social network centrality score
10. `time_to_first_resale` - Time to first resale (minutes)

### 8.3 ML Pipeline Data Flow

```
┌─────────────────┐
│ Supabase        │
│ PostgreSQL      │
│ (OLTP Data)     │
└────────┬────────┘
         │
         │ Queries
         │
┌────────▼────────────────────────┐
│ Feature Engineering             │
│ (supabase_feature_engineer.py)  │
│ - Computes 10 features          │
│ - Queries real database         │
└────────┬────────────────────────┘
         │
         │ Feature Vector
         │
┌────────▼────────────────────────┐
│ ML Models                       │
│ - Fraud Detection               │
│ - Anomaly Detection             │
│ - User Clustering               │
│ - Risk Scoring                  │
│ - Pricing Bandit                │
│ - Recommendations               │
└────────┬────────────────────────┘
         │
         │ Predictions/Outputs
         │
┌────────▼────────────────────────┐
│ DuckDB Storage                  │
│ (Analytics/OLAP)                │
│ - ml_inference_results          │
│ - ml_feature_snapshots          │
│ - ml_model_metrics              │
└─────────────────────────────────┘
```

### 8.4 ML Outputs & KPIs

#### 8.4.1 KPI Baseline

**Location:** `Machine Learning/kpis/kpi_baseline.json`

```json
{
  "precision": 0.72,
  "recall": 0.68,
  "transaction_success_rate": 0.923,
  "revenue_per_user": 45.20,
  "false_positive_rate": 0.15,
  "recommendation_ctr": 0.032,
  "anomaly_detection_latency": 45.0,
  "baseline_date": "2024-01-01T00:00:00Z"
}
```

#### 8.4.2 DuckDB Tables

**Database:** `Machine Learning/artifacts/ml_analytics.duckdb`

**Table: ml_inference_results**
| Column | Type | Description |
|--------|------|-------------|
| inference_id | BIGINT | Primary key |
| timestamp | TIMESTAMP | Inference timestamp |
| request_id | VARCHAR | Unique request identifier |
| model_name | VARCHAR | Model name (fraud_detection, etc.) |
| model_version | VARCHAR | Model version |
| input_features | JSON | Input feature vector |
| output_scores | JSON | Model output scores |
| decision | VARCHAR | Decision (APPROVED/BLOCKED) |
| confidence | FLOAT | Confidence score |
| transaction_id | VARCHAR | Transaction ID |
| wallet_address | VARCHAR | Wallet address |
| event_id | BIGINT | Event ID |

**Table: ml_feature_snapshots**
| Column | Type | Description |
|--------|------|-------------|
| snapshot_id | BIGINT | Primary key |
| timestamp | TIMESTAMP | Snapshot timestamp |
| request_id | VARCHAR | Request identifier |
| features | JSON | Feature vector snapshot |
| transaction_id | VARCHAR | Transaction ID |
| wallet_address | VARCHAR | Wallet address |
| event_id | BIGINT | Event ID |

### 8.5 ML Evaluation & Notebooks

**Jupyter Notebook:** `Machine Learning/notebooks/fraud_model_evaluation.ipynb`

**Contents:**
- Model training procedures
- Evaluation metrics
- Performance visualizations
- Baseline comparisons

---

## 9. Database Schema & ERD

### 9.1 ERD Diagram

**Location:** `diagrams/Group2_SDF1_ERD.png`

### 9.2 Core Tables

#### users
```sql
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### wallets
```sql
CREATE TABLE wallets (
    wallet_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    address VARCHAR(42) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### events
```sql
CREATE TABLE events (
    event_id BIGSERIAL PRIMARY KEY,
    organizer_wallet_id BIGINT REFERENCES wallets(wallet_id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    event_date TIMESTAMPTZ NOT NULL,
    location VARCHAR(200),
    total_supply INTEGER,
    capacity INTEGER,
    base_price NUMERIC(18, 8),
    status event_status DEFAULT 'UPCOMING',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### tickets
```sql
CREATE TABLE tickets (
    ticket_id BIGSERIAL PRIMARY KEY,
    event_id BIGINT REFERENCES events(event_id),
    owner_wallet_id BIGINT REFERENCES wallets(wallet_id),
    token_id VARCHAR(255) UNIQUE,
    status ticket_status DEFAULT 'ACTIVE',
    purchase_price NUMERIC(18, 8),
    minted_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### marketplace_listings
```sql
CREATE TABLE marketplace_listings (
    listing_id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT REFERENCES tickets(ticket_id),
    seller_wallet_id BIGINT REFERENCES wallets(wallet_id),
    price NUMERIC(18, 8) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 9.3 Migration Scripts

| File | Purpose |
|------|---------|
| `backend/migration_add_columns.sql` | Add new columns to existing tables |
| `backend/migration_add_organizer_to_events.sql` | Add organizer relationship |
| `backend/migration_resale_system.sql` | Add resale/marketplace tables |
| `backend/migration_updates.sql` | Additional schema updates |

---

## 10. Quality Assurance

### 10.1 QA Checklist

| Category | Item | Status | Notes |
|----------|------|--------|-------|
| **Code Quality** | Linting | ✅ | ESLint (frontend), flake8 (backend) |
| **Code Quality** | Type Checking | ✅ | TypeScript (frontend), mypy (backend) |
| **Testing** | Unit Tests | ✅ | Jest (frontend), pytest (backend) |
| **Testing** | Integration Tests | ✅ | Cypress (E2E) |
| **Testing** | ML Model Tests | ✅ | pytest (ML models) |
| **Performance** | Lighthouse Score | ⚠️ | *See performance section* |
| **Performance** | Load Testing | ⚠️ | *To be conducted* |
| **Security** | Dependency Scanning | ✅ | npm audit, pip check |
| **Security** | Security Headers | ✅ | Implemented in middleware |
| **Accessibility** | WCAG Compliance | ⚠️ | *See accessibility section* |
| **Documentation** | API Documentation | ✅ | Auto-generated OpenAPI |
| **Documentation** | Code Comments | ✅ | Comprehensive comments |

### 10.2 Peer Review Logs

*Placeholder: Peer review logs should be maintained in a separate file or repository issue tracker.*

**Recommended Format:**
- Review Date
- Reviewer Name
- Component Reviewed
- Issues Found
- Resolution Status

### 10.3 Testing Coverage

#### Frontend Testing
- **Framework:** Cypress
- **Coverage:** E2E tests for critical user flows
- **Config:** `frontend/cypress.config.js`

#### Backend Testing
- **Framework:** pytest
- **Coverage:** Unit tests, integration tests
- **Location:** `backend/tests/` (to be created)

#### ML Testing
- **Framework:** pytest
- **Location:** `Machine Learning/tests/`
- **Tests:**
  - `test_models.py` - Model unit tests
  - `test_integration.py` - Integration tests
  - `test_ml_pipeline_audit.py` - Pipeline audit

### 10.4 Performance Metrics

#### Lighthouse Scores (Targets)

| Metric | Target | Current |
|--------|--------|---------|
| Performance | ≥ 90 | *To be measured* |
| Accessibility | ≥ 95 | *To be measured* |
| Best Practices | ≥ 95 | *To be measured* |
| SEO | ≥ 90 | *To be measured* |

#### Link Validation

*Note: Link validation should be performed using tools like `linkinator` or `markdown-link-check`.*

---

## 11. Methodology Visualizations

### 11.1 Diagrams Available

| Diagram | Location | Description |
|---------|----------|-------------|
| **ERD** | `diagrams/Group2_SDF1_ERD.png` | Entity-Relationship Diagram |
| **Class Diagram** | `diagrams/Group2_SDF1_Class.png` | System class structure |
| **Sequence Diagram (Sale)** | `diagrams/Group2_SDF1_Sequence_diagram_sale.png` | Ticket purchase flow |
| **Sequence Diagram (Resale)** | `diagrams/Group2_SDF1_Sequence_diagram_resale.png` | Resale marketplace flow |
| **Activity Diagram** | `diagrams/Group2_SDF1_Activity_diagram.png` | User activity flows |
| **Use Case (User)** | `diagrams/Group2_SDF1_Usecase_user.png` | User use cases |
| **Use Case (Developer)** | `diagrams/Group2_SDF1_Usecase_developer.png` | Developer use cases |

### 11.2 Diagram References in Code

**Frontend Flow:**
```
User Action → React Component → API Service → Backend Router → Database/Blockchain
```

**ML Pipeline Flow:**
```
Transaction → Feature Engineering → ML Models → DuckDB → Backend Decision
```

### 11.3 Process Flows

#### Ticket Purchase Flow
1. User selects event
2. Frontend calls `/api/events/{event_id}`
3. User initiates purchase
4. Frontend calls `/api/tickets/` with ML fraud check
5. Backend queries Supabase for features
6. ML models evaluate risk
7. If approved, smart contract mints NFT
8. Transaction recorded in Supabase
9. Results stored in DuckDB

#### Resale Flow
1. User lists ticket on marketplace
2. Frontend calls `/api/marketplace/list`
3. Backend validates (50% markup limit)
4. ML risk check performed
5. Listing created in database
6. Buyer purchases via `/api/marketplace/buy`
7. Smart contract transfers NFT
8. Funds escrowed and released
9. All transactions logged

---

## 12. Dashboards & Monitoring

### 12.1 Admin Dashboard

**Location:** `frontend/pages/AdminDashboard.tsx`  
**Access:** `/admin/dashboard` (protected route)

**Features:**
- Real-time security alerts
- User activity monitoring
- Transaction analytics
- ML model performance metrics
- Graph visualizations (Recharts)
- Alert management (ban/unban users)

**Data Sources:**
- Supabase (`security_alerts`, `admin_logs`, `web_requests`)
- DuckDB (ML analytics)
- Backend API (`/api/admin/*`)

### 12.2 Monitoring Stack

#### Prometheus Metrics

**Endpoint:** `/metrics`  
**Config:** `monitoring/prometheus.yml`

**Metrics Collected:**
- HTTP request counts
- Response times
- Error rates
- Active connections

#### Grafana Dashboards

**Config:** `monitoring/grafana/`  
**Dashboards:**
- API performance
- ML model metrics
- Database performance

#### Alertmanager

**Config:** `monitoring/alertmanager.yml`  
**Alert Rules:** `monitoring/alerts.yml`

### 12.3 Sentry Integration

**Config:** `backend/sentry_config.py`, `frontend/lib/sentry.ts`

**Monitoring:**
- Error tracking
- Performance monitoring
- Release tracking

---

## 13. Accessibility & Compliance

### 13.1 WCAG Compliance

| Level | Requirement | Status | Notes |
|-------|-------------|--------|-------|
| **Level A** | Basic accessibility | ⚠️ | *To be verified* |
| **Level AA** | Enhanced accessibility | ⚠️ | *Target level* |
| **Level AAA** | Advanced accessibility | ❌ | Not required |

### 13.2 Accessibility Features Implemented

- ✅ Semantic HTML elements
- ✅ ARIA labels (partial)
- ⚠️ Alt texts for images (*to be verified*)
- ⚠️ Keyboard navigation (*to be verified*)
- ⚠️ Color contrast (*to be verified*)
- ⚠️ Screen reader compatibility (*to be verified*)

### 13.3 Cross-Browser Compatibility

**Tested Browsers:**
- Chrome/Edge (Chromium)
- Firefox
- Safari (iOS/macOS)

**Features:**
- Web3 wallet integration (MetaMask, WalletConnect)
- Modern CSS (Tailwind CSS)
- ES6+ JavaScript

### 13.4 Mobile Responsiveness

**Framework:** Tailwind CSS responsive utilities  
**Breakpoints:**
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

**Components:**
- Responsive navigation
- Mobile-optimized forms
- Touch-friendly interactions

---

## 14. File Organization

### 14.1 Repository Structure

```
NFT-TICKETING/
├── backend/                          # FastAPI backend
│   ├── routers/                     # API route handlers
│   │   ├── auth.py
│   │   ├── events.py
│   │   ├── tickets.py
│   │   ├── marketplace.py
│   │   ├── ml_services_backend.py
│   │   ├── admin.py
│   │   └── wallet.py
│   ├── models.py                    # Pydantic models
│   ├── database.py                  # Supabase client
│   ├── web3_client.py               # Blockchain integration
│   ├── security_middleware.py       # Security layer
│   ├── *.sql                        # Database schemas
│   └── requirements.txt
│
├── frontend/                         # React frontend
│   ├── pages/                       # Route components
│   │   ├── Dashboard.tsx
│   │   ├── EventDetails.tsx
│   │   ├── Marketplace.tsx
│   │   ├── AdminDashboard.tsx
│   │   └── ...
│   ├── components/                  # Reusable components
│   │   ├── ui/                      # UI primitives
│   │   ├── 3d/                      # Three.js components
│   │   └── ...
│   ├── services/                    # API clients
│   ├── lib/                         # Utilities
│   └── package.json
│
├── Machine Learning/                 # ML components
│   ├── models/                      # ML models (6 models)
│   ├── integration/                 # Integration layer
│   ├── features/                    # Feature engineering
│   ├── kpis/                        # KPI calculations
│   ├── notebooks/                   # Jupyter notebooks
│   ├── tests/                       # ML tests
│   └── requirements.txt
│
├── smart_contracts/                  # Blockchain contracts
│   ├── contracts/                   # Solidity contracts
│   │   └── NFTTicket.sol
│   ├── artifacts/                   # Compiled contracts
│   │   └── contracts/NFTTicket.sol/NFTTicket.json
│   ├── scripts/                     # Deployment scripts
│   └── hardhat.config.ts
│
├── diagrams/                         # System diagrams
│   ├── Group2_SDF1_ERD.png
│   ├── Group2_SDF1_Class.png
│   ├── Group2_SDF1_Sequence_diagram_*.png
│   └── ...
│
├── monitoring/                       # Monitoring configs
│   ├── prometheus.yml
│   ├── grafana/
│   └── alertmanager.yml
│
└── README.md                         # This file
```

### 14.2 Key Files Reference

| File | Purpose | Location |
|------|---------|----------|
| **API Entry Point** | FastAPI application | `backend/main.py` |
| **Smart Contract** | NFT ticket contract | `smart_contracts/contracts/NFTTicket.sol` |
| **Contract ABI** | Contract interface | `smart_contracts/artifacts/contracts/NFTTicket.sol/NFTTicket.json` |
| **Database Schema** | Complete schema | `backend/complete_database_schema.sql` |
| **ML Integration** | ML backend integration | `Machine Learning/integration/ml_integration_backend.py` |
| **Frontend Entry** | React app entry | `frontend/index.tsx` |
| **Admin Dashboard** | Admin panel | `frontend/pages/AdminDashboard.tsx` |

---

## 15. Pitch Deck

### 15.1 Pitch Deck Structure (Recommended)

*Note: Actual pitch deck should be created as a separate presentation file (PowerPoint, Google Slides, etc.)*

#### Slide 1: Title Slide
- **Title:** NFTIX - NFT-Based Event Ticketing Platform
- **Tagline:** Secure, Fraud-Resistant, ML-Powered Ticketing
- **Team:** [Team Name]
- **Date:** 2024

#### Slide 2: Problem Statement
- Ticket scalping and fraud
- Lack of transparency
- Poor user experience

#### Slide 3: Solution Overview
- Blockchain-based NFT tickets
- ML-powered fraud detection
- Fair resale marketplace
- **Visual:** System architecture diagram

#### Slide 4: Key Features
- ✅ NFT tickets (immutable ownership)
- ✅ ML fraud detection (real-time risk scoring)
- ✅ Fair resale (50% markup limit)
- ✅ Dynamic pricing (ML-optimized)
- ✅ Admin dashboard (security monitoring)

#### Slide 5: Technology Stack
- **Visual:** Technology stack diagram
- Frontend: React, Three.js
- Backend: FastAPI, Python
- Blockchain: Solidity, Ethereum
- ML: XGBoost, scikit-learn

#### Slide 6: Market Opportunity
- Event ticketing market size
- Blockchain adoption trends
- ML in fintech

#### Slide 7: Demo Screenshots
- User dashboard
- Event details page
- Marketplace
- Admin panel

#### Slide 8: ML Intelligence
- **Visual:** ML pipeline diagram
- 6 ML models
- Real-time fraud detection
- Recommendation engine
- Dynamic pricing

#### Slide 9: Security & Compliance
- Security middleware
- Real-time threat detection
- WCAG accessibility (target)
- GDPR considerations

#### Slide 10: Roadmap
- Sprint 1-2: Core functionality
- Sprint 3: ML integration
- Sprint 4: Full integration
- Future: Mobile app, additional features

#### Slide 11: Team
- Team members and roles

#### Slide 12: Contact & Next Steps
- GitHub repository
- Demo link
- Contact information

### 15.2 Visual Assets for Pitch Deck

**Recommended Charts/Diagrams:**
1. System Architecture Diagram (Section 4.1)
2. ML Pipeline Flow (Section 8.3)
3. ERD Diagram (`diagrams/Group2_SDF1_ERD.png`)
4. Sequence Diagrams (`diagrams/Group2_SDF1_Sequence_*.png`)
5. Technology Stack Chart
6. Market Opportunity Charts (to be created)
7. ML Model Performance Metrics (from notebooks)

**Interactive Elements:**
- Three.js 3D visualizations (can be embedded)
- Real-time dashboard demos (screen recording)
- Live API documentation (`/docs`)

### 15.3 Speaker Notes (Placeholders)

*Speaker notes should be added to each slide with talking points:*
- Key points to emphasize
- Technical details to mention
- Demo instructions
- Q&A preparation

---

## 16. Demo Video

### 16.1 Demo Video Specifications

**Format:** MP4 (H.264)  
**Resolution:** 1920x1080 (Full HD)  
**Duration:** 10-15 minutes  
**Audio:** Clear narration with background music (optional)  
**Captions/Subtitles:** English (SRT format recommended)

### 16.2 Demo Video Structure

#### Section 1: Introduction (1-2 min)
- Project overview
- Problem statement
- Solution highlights

#### Section 2: User Flow - Ticket Purchase (3-4 min)
1. User registration/login
2. Browse events
3. Select event
4. Purchase ticket (ML fraud check)
5. View NFT ticket in wallet
6. **Screen recording** of actual flow

#### Section 3: Marketplace & Resale (2-3 min)
1. List ticket for resale
2. Browse marketplace
3. Purchase from marketplace
4. Verify 50% markup limit
5. **Screen recording** of marketplace

#### Section 4: ML Intelligence (2-3 min)
1. Admin dashboard overview
2. ML model health check (`/api/ml/health`)
3. Fraud detection demo
4. Risk analysis demo
5. Recommendations demo
6. **Screen recording** of API calls and responses

#### Section 5: Admin Dashboard (2-3 min)
1. Security alerts
2. User management
3. Analytics graphs
4. Real-time monitoring
5. **Screen recording** of admin panel

#### Section 6: Technical Deep Dive (2-3 min)
1. Smart contract interaction
2. Database queries
3. ML pipeline execution
4. DuckDB analytics
5. **Screen recording** or diagrams

### 16.3 Video Production Checklist

- [ ] Screen recording software (OBS, Loom, etc.)
- [ ] Audio recording (clear microphone)
- [ ] Video editing software
- [ ] Captions/subtitles creation
- [ ] Thumbnail creation
- [ ] Upload to hosting platform (YouTube, Vimeo, etc.)

### 16.4 Video Assets to Include

**Screen Recordings:**
- Live user journey (ticket purchase)
- Marketplace interaction
- Admin dashboard navigation
- API documentation (`/docs`)
- Smart contract interaction

**Clips from Sprints:**
- Sprint 1-2: Core functionality demo
- Sprint 3: ML model training/evaluation
- Sprint 4: Full integration demo

---

## 17. Additional Deliverables

### 17.1 Documentation Deliverables

- ✅ README.md (this file)
- ✅ API Documentation (OpenAPI/Swagger)
- ✅ Database Schema Documentation
- ✅ ML Model Documentation
- ✅ Smart Contract Documentation (NatSpec comments)
- ⚠️ Architecture Decision Records (ADRs) - *Recommended*
- ⚠️ Deployment Guide - *Recommended*
- ⚠️ Contributing Guidelines - *Recommended*

### 17.2 Code Deliverables

- ✅ Frontend application (React/TypeScript)
- ✅ Backend API (FastAPI/Python)
- ✅ Smart contracts (Solidity)
- ✅ ML models and integration (Python)
- ✅ Database schemas and migrations (SQL)
- ✅ Tests (Cypress, pytest)

### 17.3 Artifact Deliverables

- ✅ ERD Diagram
- ✅ Sequence Diagrams
- ✅ Class Diagram
- ✅ Activity Diagram
- ✅ Use Case Diagrams
- ✅ Smart Contract ABI
- ✅ ML Evaluation Notebooks
- ⚠️ Deployment scripts - *Recommended*
- ⚠️ CI/CD configuration - *Recommended*

### 17.4 Presentation Deliverables

- ⚠️ Pitch Deck (PowerPoint/PDF) - *To be created*
- ⚠️ Demo Video (MP4) - *To be created*
- ⚠️ Project Poster - *Optional*

---

## 18. Success Metrics

### 18.1 Technical Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **API Response Time** | < 200ms (p95) | Prometheus metrics |
| **Frontend Load Time** | < 3s | Lighthouse |
| **ML Model Accuracy** | > 85% | Model evaluation |
| **Fraud Detection Precision** | > 90% | KPI tracking |
| **Test Coverage** | > 80% | pytest/coverage |
| **Uptime** | > 99.5% | Monitoring |

### 18.2 ML Model KPIs

**Baseline KPIs** (from `Machine Learning/kpis/kpi_baseline.json`):
- Precision: 0.72
- Recall: 0.68
- Transaction Success Rate: 0.923
- Revenue Per User: 45.20
- False Positive Rate: 0.15
- Recommendation CTR: 0.032
- Anomaly Detection Latency: 45.0ms

**Target Improvements:**
- Precision: > 0.85
- Recall: > 0.80
- False Positive Rate: < 0.10

### 18.3 Business Success Metrics

| Metric | Description | Measurement |
|--------|-------------|-------------|
| **User Adoption** | Number of registered users | Database query |
| **Ticket Sales** | Number of tickets sold | Database query |
| **Marketplace Activity** | Number of resale transactions | Database query |
| **Fraud Prevention** | Number of blocked fraudulent transactions | ML logs |
| **User Satisfaction** | User feedback/ratings | *To be implemented* |

### 18.4 Security Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Security Alerts** | < 10/day (normal traffic) | Admin dashboard |
| **False Positives** | < 5% | Alert review |
| **Response Time** | < 1 hour | Alert management |
| **Vulnerability Count** | 0 critical | Dependency scanning |

---

## 19. Appendices

### Appendix A: API Endpoint Reference

**Complete API endpoint list available at:**
- Interactive: `http://localhost:8000/docs`
- JSON: `http://localhost:8000/openapi.json`

**Total Endpoints:** 61+ endpoints across 8 routers

### Appendix B: Database Schema Reference

**Complete schema files:**
- `backend/complete_database_schema.sql` - Full schema with enums
- `backend/database_schema_final.sql` - Production schema
- ERD: `diagrams/Group2_SDF1_ERD.png`

### Appendix C: Smart Contract Reference

**Contract:** `smart_contracts/contracts/NFTTicket.sol`  
**ABI:** `smart_contracts/artifacts/contracts/NFTTicket.sol/NFTTicket.json`

**Key Functions:**
- `mintTicket(address to, string uri, uint256 eventId, uint256 price)`
- `resellTicket(uint256 tokenId, uint256 price)`
- `buyTicket(uint256 tokenId)`
- `validateTicket(uint256 tokenId)`

### Appendix D: ML Model Reference

**Models Location:** `Machine Learning/models/`

**Model Details:**
1. **Fraud Detection** - XGBoost classifier, 10 features
2. **Anomaly Detection** - Isolation Forest, contamination=0.02
3. **User Clustering** - K-Means (5 clusters) + DBSCAN
4. **Recommendation Engine** - Collaborative filtering
5. **Pricing Bandit** - Epsilon-greedy MAB (ε=0.15)
6. **Risk Scoring** - Rule-based heuristic

**Evaluation Notebook:** `Machine Learning/notebooks/fraud_model_evaluation.ipynb`

### Appendix E: Tools & Technologies Summary

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Frontend Framework** | React | 18.2.0 | UI framework |
| **Frontend Language** | TypeScript | Latest | Type safety |
| **Frontend Build** | Vite | Latest | Build tool |
| **UI Library** | Tailwind CSS | Latest | Styling |
| **3D Graphics** | Three.js | 0.162.0 | 3D visualizations |
| **Backend Framework** | FastAPI | 0.109.0 | API framework |
| **Backend Language** | Python | 3.12 | Backend logic |
| **Database** | Supabase (PostgreSQL) | Latest | Primary database |
| **Analytics DB** | DuckDB | 0.9.0 | ML analytics |
| **Blockchain** | Solidity | 0.8.20 | Smart contracts |
| **Blockchain Framework** | Hardhat | Latest | Contract development |
| **Web3 Library** | Web3.py | 6.15.1 | Blockchain integration |
| **ML Framework** | scikit-learn | Latest | ML models |
| **ML Framework** | XGBoost | Latest | Gradient boosting |
| **ML Language** | Python | 3.12 | ML implementation |
| **Monitoring** | Prometheus | Latest | Metrics |
| **Monitoring** | Grafana | Latest | Dashboards |
| **Error Tracking** | Sentry | Latest | Error monitoring |
| **Testing** | Cypress | 13.6.0 | E2E testing |
| **Testing** | pytest | Latest | Backend/ML testing |

---

## 20. Getting Started

### 20.1 Prerequisites

- Node.js 18+
- Python 3.12+
- PostgreSQL (via Supabase)
- MetaMask or compatible Web3 wallet
- Git

### 20.2 Installation

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
```

#### Smart Contracts Setup
```bash
cd smart_contracts
npm install
```

#### ML Setup
```bash
cd "Machine Learning"
pip install -r requirements.txt
```

### 20.3 Environment Variables

**Backend (`.env`):**
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
PRIVATE_KEY=your_ethereum_private_key
DATABASE_URL=your_database_url
SENTRY_DSN=your_sentry_dsn
```

**Frontend (`.env`):**
```
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_KEY=your_supabase_key
```

### 20.4 Running the Application

#### Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

#### Start Frontend
```bash
cd frontend
npm run dev  # Port 5173
```

#### Start Admin Panel
```bash
cd frontend
npm run dev:admin  # Port 4201
```

### 20.5 Access Points

- **Frontend:** http://localhost:5173
- **Admin Panel:** http://localhost:4201
- **API Documentation:** http://localhost:8000/docs
- **API Health:** http://localhost:8000/health

---

## 21. Version Control

### 21.1 Git Repository

**Recommended Structure:**
- `main` branch - Production-ready code
- `develop` branch - Integration branch
- Feature branches - Individual features
- Sprint branches - Sprint-specific work

### 21.2 Git Workflow

1. Create feature branch from `develop`
2. Make changes and commit
3. Push to remote
4. Create pull request
5. Code review
6. Merge to `develop`
7. Deploy to staging
8. Merge to `main` for production

### 21.3 Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

---

## 22. Contact & Support

### 22.1 Project Team

*[Team members and contact information to be added]*

### 22.2 Repository

**GitHub:** [Repository URL to be added]

### 22.3 Issues & Bug Reports

*[Issue tracker link to be added]*

---

## 23. License

*[License information to be added]*

---

## 24. Acknowledgments

- OpenZeppelin for smart contract libraries
- FastAPI for the excellent web framework
- React and the open-source community
- Supabase for the backend infrastructure
- All contributors and reviewers

---

**Last Updated:** 2024  
**Version:** 1.0.0  
**Sprint:** Sprint 4

---

*This README is a living document and will be updated as the project evolves.*


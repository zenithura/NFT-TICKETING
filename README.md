
# NFT-TICKETING

A comprehensive NFT ticketing platform combining blockchain technology, advanced data science, and modern web development. The project features Ethereum smart contracts for NFT ticket minting and resale, a React frontend with admin capabilities, a FastAPI backend with ML-powered fraud detection, and integrated monitoring systems.

**Key Features**

- **Blockchain Integration**: NFT-based ticket minting, transfers, and resale on Ethereum
- **Dual Frontend**: Main user interface and dedicated admin dashboard
- **Advanced Backend**: FastAPI with Supabase integration, authentication, and Web3 connectivity
- **ML & Data Science**: Bot detection, fraud prevention, price fairness, market trends, and user segmentation
- **Security & Monitoring**: Sentry integration, Prometheus metrics, attack tracking, and real-time monitoring
- **Comprehensive Testing**: Backend pytest suite, frontend Cypress tests, and smart contract tests

**Quick links**

- Smart contracts: `smart_contracts/`
- Frontend (Vite + React): `frontend/`
- Backend (FastAPI): `backend/`
- Data Science & ML: `backend/data_science/`
- Monitoring Dashboard: `backend/monitoring/`
- Documentation: `docs/`
- Project Analysis: `docs/PROJECT_ANALYSIS.md`

## Table of Contents

- [NFT-TICKETING](#nft-ticketing)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Prerequisites](#prerequisites)
  - [Quickstart — Local Development](#quickstart--local-development)
    - [1. Smart Contracts](#1-smart-contracts)
    - [2. Backend Setup](#2-backend-setup)
    - [3. Frontend Development](#3-frontend-development)
  - [Smart Contracts](#smart-contracts)
  - [Backend Services](#backend-services)
    - [API Endpoints](#api-endpoints)
    - [Key Features](#key-features)
    - [Configuration](#configuration)
  - [Frontend Applications](#frontend-applications)
    - [Main User Interface](#main-user-interface)
    - [Admin Dashboard](#admin-dashboard)
  - [Data Science \& ML](#data-science--ml)
    - [Models](#models)
    - [Components](#components)
    - [Monitoring Dashboard](#monitoring-dashboard)
  - [Testing](#testing)
    - [Backend Tests](#backend-tests)
    - [Frontend Tests](#frontend-tests)
    - [Smart Contract Tests](#smart-contract-tests)
  - [Deployment](#deployment)
    - [Production Build](#production-build)
    - [Environment-Specific Configuration](#environment-specific-configuration)
  - [Documentation](#documentation)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Performance Optimization](#performance-optimization)
  - [Contributing](#contributing)
    - [Code Standards](#code-standards)
  - [License](#license)

## Project Structure

```
NFT-TICKETING/
├── smart_contracts/        # Ethereum smart contracts (Hardhat)
│   ├── contracts/         # Solidity contracts (NFTTicket.sol)
│   ├── test/             # Smart contract tests
│   └── scripts/          # Deployment scripts
├── frontend/              # Main user interface
│   ├── components/       # React components
│   ├── pages/           # Application pages
│   ├── services/        # API & Web3 services
│   └── cypress/         # E2E tests
├── backend/               # FastAPI backend
│   ├── routers/         # API endpoints (auth, events, tickets, marketplace, admin, ML)
│   ├── data_science/    # ML models and pipelines
│   ├── monitoring/      # Monitoring dashboard and APIs
│   ├── migrations/      # Database migration scripts
│   ├── tests/          # Backend test suite
│   └── config/         # Configuration files
├── docs/                  # Project documentation
│   ├── project_whitepaper.md
│   ├── investor_pitch_deck.md
│   └── qa_report.md
└── logs/                 # Application logs
```

## Prerequisites

- **Node.js** v18+ (for frontend and smart contracts)
- **npm** or **yarn** (package management)
- **Python** 3.11+ (backend and data science)
- **PostgreSQL** (via Supabase or local installation)
- **Redis** (for caching, optional but recommended)
- **Docker** (optional, for containerized services)

**Development Tools**

- Hardhat (smart contract development)
- MetaMask or compatible Web3 wallet
- Git for version control

## Quickstart — Local Development

### 1. Smart Contracts

```bash
cd smart_contracts
npm install
npx hardhat compile
npx hardhat test

# Start local Ethereum node
npx hardhat node

# Deploy contracts (in new terminal)
npx hardhat run scripts/deploy.ts --network localhost
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Supabase credentials and other settings

# Run database migrations
python -m scripts.run_migrations

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Development

```bash
cd frontend
npm install

# Start main user interface
npm run dev

# Start admin dashboard (in separate terminal)
npm run dev:admin
```

The main app runs at `http://localhost:5173` and admin dashboard at a different port.

## Using the Database and Site with Data

To fully experience the platform's features, especially the ML-powered fraud detection and analytics, you need to populate the database with data.

### 1. Populating Synthetic Data
The backend includes scripts to generate and populate the database with synthetic events, tickets, and transactions.

```bash
cd backend
source venv/bin/activate

# Generate synthetic data for events and users
python -m scripts.generate_synthetic_data

# Populate local data for ML models
python -m scripts.populate_local_data
```

### 2. Training ML Models
Once data is populated, you can run the training pipeline to generate model artifacts.

```bash
cd backend
source venv/bin/activate
python -m data_science.pipelines.training_pipeline
```

### 3. Running the Full Stack
Use the provided `run_all.sh` script to start all services simultaneously.

```bash
./run_all.sh
```

This script starts:
- Hardhat Node (Blockchain)
- Contract Deployment
- Monitoring Dashboard
- FastAPI Backend
- React Frontend

### 4. Verifying Data Flow
- **Frontend**: Browse events at `http://localhost:5173`.
- **Admin Dashboard**: View analytics and fraud detection results.
- **Monitoring**: Check `http://localhost:8050` (default) for the real-time monitoring dashboard.

## Smart Contracts

The project uses OpenZeppelin contracts for secure NFT implementation.

**Main Contract**: `NFTTicket.sol`
- ERC721 compliant NFT tickets
- Minting with metadata
- Transfer restrictions and resale logic
- Event and venue management

**Commands**:
```bash
cd smart_contracts
npx hardhat compile        # Compile contracts
npx hardhat test          # Run tests
npx hardhat node          # Local blockchain
npx hardhat run scripts/deploy.ts --network <network>
```

## Backend Services

Built with **FastAPI**, the backend provides:

### API Endpoints

- **Authentication** (`/auth`): User registration, login, JWT tokens
- **Events** (`/events`): Create, list, and manage events
- **Tickets** (`/tickets`): Mint, transfer, and validate tickets
- **Marketplace** (`/marketplace`): Resale listings and purchases
- **Wallet** (`/wallet`): Web3 wallet operations
- **ML Services** (`/ml`): Fraud detection, price prediction, recommendations
- **Admin** (`/admin`): Administrative functions and monitoring

### Key Features

- **Supabase Integration**: PostgreSQL database with real-time capabilities
- **Web3 Connectivity**: Smart contract interaction via web3.py
- **Authentication**: JWT-based auth with role-based access control
- **Caching**: Redis integration for performance
- **Security Middleware**: Rate limiting, attack tracking, CORS
- **Monitoring**: Sentry error tracking, Prometheus metrics
- **Logging**: Comprehensive logging system with JSONL output

### Configuration

Environment variables (`.env`):
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
JWT_SECRET=your_jwt_secret
WEB3_PROVIDER_URL=http://localhost:8545
REDIS_URL=redis://localhost:6379
SENTRY_DSN=your_sentry_dsn
```

## Frontend Applications

### Main User Interface

Built with **React 18**, **Vite**, **TypeScript**, and **TailwindCSS**.

**Features**:
- Event browsing and ticket purchasing
- NFT wallet integration (MetaMask)
- Ticket resale marketplace
- QR code ticket scanning
- Internationalization (i18n)
- Performance optimized with code splitting

**Scripts**:
```bash
npm run dev              # Development server
npm run build           # Production build
npm run preview         # Preview production build
npm run test           # Run Cypress tests
npm run e2e            # E2E tests in browser
```

### Admin Dashboard

Separate admin interface for event organizers and system administrators.

```bash
npm run dev:admin       # Development
npm run build:admin     # Production build
```

**Admin Features**:
- Event and venue management
- User management and analytics
- Fraud detection dashboard
- System monitoring and metrics
- Financial reporting

## Data Science & ML

Located in `backend/data_science/`, the ML pipeline provides intelligent features:

### Models

1. **Bot Detection**: Identifies automated/bot accounts
2. **Risk Scoring**: Assigns risk scores to transactions
3. **Fair Price Model**: Determines fair market prices
4. **Scalping Detection**: Detects ticket scalping behavior
5. **Wash Trading Detection**: Identifies suspicious trading patterns
6. **Recommender System**: Personalized event recommendations
7. **User Segmentation**: Customer segmentation for marketing
8. **Market Trend Analysis**: Predicts market trends
9. **Decision Rules**: Automated decision-making engine

### Components

- **Data Loader**: Loads data from Supabase for training
- **Feature Store**: Manages ML features
- **Pipelines**: Training and inference pipelines
- **Core**: KPI calculator, A/B testing, data logger
- **Artifacts**: Trained model storage

### Monitoring Dashboard

Real-time monitoring at `backend/monitoring/`:
- System metrics and alerts
- Fraud detection dashboard
- Performance monitoring
- Custom alert rules

## Testing

### Backend Tests

```bash
cd backend
pytest                          # All tests
pytest tests/test_auth.py      # Specific test file
pytest --cov                    # With coverage
pytest -v -s                    # Verbose output
```

### Frontend Tests

```bash
cd frontend
npm run test                    # Run Cypress tests
npm run e2e                     # Interactive E2E testing
npm run e2e:headless           # Headless E2E tests
```

### Smart Contract Tests

```bash
cd smart_contracts
npx hardhat test
npx hardhat coverage           # Test coverage
```

## Deployment

### Production Build

**Frontend**:
```bash
cd frontend
npm run build                  # Main app
npm run build:admin           # Admin dashboard
```

**Backend**:
```bash
# Using gunicorn for production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Smart Contracts**:
```bash
# Deploy to testnet/mainnet
npx hardhat run scripts/deploy.ts --network sepolia
```

### Environment-Specific Configuration

- Development: `.env.development`
- Staging: `.env.staging`
- Production: `.env.production`

## Documentation

The `docs/` directory contains comprehensive documentation:

- **project_whitepaper.md**: Technical whitepaper
- **investor_pitch_deck.md**: Business presentation
- **pitch_speech.md**: Pitch script
- **qa_report.md**: Quality assurance documentation
- **PROJECT_ANALYSIS.md**: Detailed analysis of fixed problematic areas
- **traceability_matrix.md**: Requirements traceability

## Troubleshooting

### Common Issues

**Smart Contracts**

- **Port 8545 already in use**: Stop any existing Hardhat nodes
  ```bash
  pkill -f "hardhat node"
  ```
- **Contract deployment fails**: Ensure local node is running first
- **Transaction reverted**: Check account has sufficient ETH

**Backend**

- **Supabase connection errors**: Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- **Module import errors**: Ensure virtual environment is activated and dependencies installed
  ```bash
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- **Database errors**: Run migrations with `python -m scripts.run_migrations`
- **Port 8000 in use**: Change port or kill existing process

**Frontend**

- **Build failures**: Clear node_modules and reinstall
  ```bash
  rm -rf node_modules package-lock.json
  npm install
  ```
- **MetaMask not connecting**: Check network ID matches local Hardhat node (usually 31337)
- **API errors**: Ensure backend is running on port 8000

**Data Science**

- **Model loading errors**: Check `artifacts/` directory has trained models
- **Redis connection failed**: Install and start Redis or disable caching

### Performance Optimization

- Enable Redis caching for better API response times
- Use production builds for frontend (`npm run build`)
- Configure database indexes (see `backend/database_indexes.sql`)
- Monitor with Sentry and Prometheus metrics

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes** with clear commit messages
4. **Add tests** for new functionality
5. **Run the test suite** to ensure everything passes
6. **Submit a pull request** to the `main` branch

### Code Standards

- **Python**: Follow PEP 8, use type hints
- **TypeScript/React**: Follow ESLint configuration
- **Solidity**: Follow Solidity style guide
- **Commits**: Use conventional commit messages

## License

This project is currently proprietary. Please contact the repository owner for licensing information.

---

**For questions, issues, or feature requests**, please open an issue on the repository or contact the development team.

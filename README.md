<div align="center">

# 🎫 NFT-TICKETING

### Next-Generation Blockchain Ticketing Platform

[![Solidity](https://img.shields.io/badge/Solidity-%5E0.8.0-363636?logo=solidity)](https://soliditylang.org/)
[![Hardhat](https://img.shields.io/badge/Hardhat-Tests%20Passing-yellow?logo=ethereum)](smart-contracts/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=white)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**A complete NFT ticketing ecosystem with smart contracts, modern React frontend, optional Python backend, and ML-powered fraud detection.**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Documentation](#-documentation) • [Demo](#-demo--testing)

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📦 What's Inside](#-whats-inside)
- [🏗️ Architecture](#️-architecture)
- [💻 Development Setup](#-development-setup)
- [🎬 Demo & Testing](#-demo--testing)
- [🔧 Configuration](#-configuration)
- [🐛 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎟️ **Smart Contract Capabilities**
- ✅ Mint NFT tickets with event metadata
- ✅ Primary & secondary market support
- ✅ Resale with price controls & royalties
- ✅ QR code scanning & validation
- ✅ Batch operations & gas optimization
- ✅ Comprehensive test coverage (14+ tests)

</td>
<td width="50%">

### 🎨 **Frontend Features**
- ✅ Modern React 18 + TypeScript + Vite
- ✅ MetaMask & wallet integration
- ✅ Real-time marketplace with filters
- ✅ Event creation & management dashboard
- ✅ Ticket scanner interface
- ✅ Responsive mobile-first design

</td>
</tr>
<tr>
<td width="50%">

### 🔐 **Security & Data**
- ✅ FastAPI backend with Supabase
- ✅ ML fraud detection (Sprint3)
- ✅ Rate limiting & authentication
- ✅ Database migrations & seed data
- ✅ Redis caching layer
- ✅ Real-time monitoring dashboard

</td>
<td width="50%">

### 🛠️ **Developer Experience**
- ✅ One-command local setup
- ✅ Hot reload for all components
- ✅ Automated deployment scripts
- ✅ Docker Compose orchestration
- ✅ Comprehensive documentation
- ✅ End-to-end demo flows

</td>
</tr>
</table>

---

## 🚀 Quick Start

Get the entire stack running in **3 minutes**:

### Prerequisites

```bash
# Required
Node.js 16+    │  npm or yarn
Python 3.8+    │  Docker (for Sprint3)

# Optional
jq, curl       │  MetaMask browser extension
```

### One-Command Setup

```bash
# Clone and navigate
git clone https://github.com/zenithura/NFT-TICKETING.git
cd NFT-TICKETING

# Option 1: Auto-start everything (requires tmux)
./run_all.sh

# Option 2: Manual start (recommended for first-time)
# See detailed setup below ⬇️
```

---

## 📦 What's Inside

```
NFT-TICKETING/
├── 📜 smart-contracts/        # Solidity contracts + Hardhat
│   ├── contracts/             # TicketManager.sol (core NFT logic)
│   ├── test/                  # Comprehensive test suite
│   ├── scripts/               # Deployment automation
│   └── artifacts/             # Compiled contracts & ABIs
│
├── 🎨 frontend/               # React + TypeScript + Vite
│   ├── src/                   # Application source
│   ├── components/            # Reusable UI components
│   ├── pages/                 # Route pages (Dashboard, Marketplace, etc.)
│   └── services/              # Web3 & API integrations
│
├── 🐍 frontend_with_backend/  # Alternative setup with backend
│   ├── backend/               # FastAPI + Supabase
│   │   ├── server.py          # Main API server
│   │   ├── blockchain.py      # Web3 service layer
│   │   └── *.sql              # Database migrations
│   └── frontend/              # Legacy React frontend
│
├── 📊 sprint3/                # Data science & security layer
│   ├── docker-compose.yml     # Multi-service orchestration
│   ├── ml_pipeline/           # Fraud detection models
│   ├── api/                   # Fraud detection API
│   └── monitoring/            # Dash analytics dashboard
│
├── 📄 demo.sh                 # End-to-end demo script
├── 🐍 blockchain_demo.py      # Python demo runner
└── 📖 README.md              # You are here!
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  👤 Browser/Mobile  →  MetaMask Wallet  →  Web3 Provider       │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                              │
│  🎨 React App (Vite) - TypeScript - TailwindCSS                │
│  ├─ Event Browser        ├─ Marketplace      ├─ Admin Panel   │
│  ├─ Ticket Purchase      ├─ Resale Listings  └─ Scanner UI    │
└─────────────────────────────────────────────────────────────────┘
                    ↓                           ↓
┌──────────────────────────────┐  ┌──────────────────────────────┐
│    BLOCKCHAIN LAYER          │  │    BACKEND LAYER (Optional)  │
│  ⛓️  Smart Contracts         │  │  🐍 FastAPI Server           │
│  └─ TicketManager.sol        │  │  ├─ REST API endpoints       │
│     ├─ Minting               │  │  ├─ Web3 integration         │
│     ├─ Transfers             │  │  └─ Business logic           │
│     ├─ Marketplace           │  └──────────────────────────────┘
│     └─ Scanning              │                ↓
└──────────────────────────────┘  ┌──────────────────────────────┐
                                   │    DATABASE LAYER            │
                                   │  🗄️  Supabase/PostgreSQL     │
                                   │  ├─ Events, Venues, Users    │
                                   │  ├─ Orders & Transactions    │
                                   │  └─ Analytics                │
                                   └──────────────────────────────┘
                                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                   SPRINT3: SECURITY & ML LAYER                   │
│  🔐 Fraud Detection  │  📊 Monitoring  │  ⚡ Redis Cache        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Development Setup

### Step 1: Smart Contracts

```bash
cd smart-contracts

# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Run tests (14 tests should pass)
npx hardhat test

# Start local blockchain (keep this running)
npx hardhat node

# Deploy to local network (new terminal)
npx hardhat run scripts/deploy.js --network localhost
```

**Expected Output:**
```
✓ 14 passing (2s)
Deploying contracts with account: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
TicketManager deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3
```

### Step 2: Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Access:** Open browser to `http://localhost:3000` (or `http://localhost:5173`)

### Step 3: Backend (Optional)

```bash
cd frontend_with_backend/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (see Configuration section)
cp .env.example .env
# Edit .env with your SUPABASE_URL and SUPABASE_KEY

# Start server
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Access:** API docs at `http://localhost:8000/docs`

### Step 4: Sprint3 Stack (Optional)

```bash
cd sprint3

# Start all services (Postgres, Redis, Fraud API, Dashboard)
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Access:** Dashboard at `http://localhost:8050`

---

## 🎬 Demo & Testing

### Automated Demo

```bash
# Ensure Hardhat node, backend, and frontend are running
bash demo.sh
```

This script will:
1. ✅ Check all services are running
2. ✅ Create a test wallet
3. ✅ Create a venue and event
4. ✅ Mint an NFT ticket
5. ✅ Verify blockchain transaction
6. ✅ Display ticket in wallet

### Manual Testing Flow

1. **Connect Wallet**: Click "Connect Wallet" in frontend
2. **Create Event**: Navigate to Admin → Create Event
3. **Purchase Ticket**: Browse events → Buy ticket
4. **View Ticket**: My Tickets → See your NFT
5. **List for Resale**: Click "Sell" → Set price
6. **Scan Ticket**: Scanner page → Scan QR code

### Run Tests

```bash
# Smart contract tests
cd smart-contracts
npx hardhat test

# Coverage report
npx hardhat coverage

# Frontend tests (if available)
cd frontend
npm test

# Backend tests (if available)
cd frontend_with_backend/backend
pytest
```

---

## 🔧 Configuration

### Environment Variables

**Backend** (`frontend_with_backend/backend/.env`):
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Optional: Web3 Provider
INFURA_KEY=your-infura-key
ALCHEMY_KEY=your-alchemy-key

# Security
JWT_SECRET=your-secret-key-min-32-chars
```

**Sprint3** (`sprint3/.env`):
```bash
# Database
DB_PASSWORD=your-db-password

# ML Model
FRAUD_THRESHOLD_BLOCK=0.85
FRAUD_THRESHOLD_REVIEW=0.65

# Monitoring
SLACK_WEBHOOK=https://hooks.slack.com/...
```

### Network Configuration

**Hardhat** (`smart-contracts/hardhat.config.js`):
```javascript
networks: {
  localhost: {
    url: "http://127.0.0.1:8545"
  },
  // Add production networks as needed
}
```

---

## 🐛 Troubleshooting

<details>
<summary><b>❌ Port already in use (8545)</b></summary>

```bash
# Find and kill process using port 8545
lsof -ti:8545 | xargs kill -9

# Or use a different port
npx hardhat node --port 8546
```
</details>

<details>
<summary><b>❌ MetaMask not connecting</b></summary>

1. Reset account in MetaMask (Settings → Advanced → Reset Account)
2. Ensure correct network selected (Localhost:8545)
3. Check browser console for errors
</details>

<details>
<summary><b>❌ Backend database errors</b></summary>

```bash
# Verify Supabase credentials
curl -H "apikey: YOUR_KEY" YOUR_SUPABASE_URL/rest/v1/

# Check backend logs
cd frontend_with_backend/backend
python server.py  # Run in foreground to see errors
```
</details>

<details>
<summary><b>❌ Docker Compose not available</b></summary>

```bash
# Install Docker Compose plugin
sudo apt install docker-compose-plugin

# Or use standalone
sudo apt install docker-compose
```
</details>

<details>
<summary><b>❌ Gas estimation failed</b></summary>

1. Check contract is deployed: `npx hardhat run scripts/deploy.js --network localhost`
2. Verify account has test ETH
3. Restart Hardhat node
</details>

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Keep commits atomic and descriptive

---

## 📄 License

This project is currently **unlicensed**. Add a `LICENSE` file to specify terms (MIT recommended for open-source).

---

## 📞 Contact & Support

- **Issues**: [Open an issue](https://github.com/zenithura/NFT-TICKETING/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zenithura/NFT-TICKETING/discussions)
- **Owner**: [@zenithura](https://github.com/zenithura)

---

<div align="center">

**Built with ❤️ using Solidity, React, and FastAPI**

⭐ Star this repo if you find it helpful!

[Back to Top](#-nft-ticketing)

</div>

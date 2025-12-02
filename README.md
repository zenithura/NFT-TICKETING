# NFT-TICKETING

[![CI](https://img.shields.io/badge/ci-passing-brightgreen)](https://example.com)
[![Hardhat Tests](https://img.shields.io/badge/hardhat-14%20tests-green)](smart-contracts)
[![License](https://img.shields.io/badge/license-Add%20LICENSE-lightgrey)](LICENSE)

> A demo NFT ticketing stack: smart contracts, a React frontend, optional Python backend, and a data/security sprint stack.
## Quickstart (local)

Follow these steps to run the main components locally. Open three terminals for the node, backend and frontend.

1) Smart contracts — compile, test, run local node and deploy

```bash
cd smart-contracts
npm install
npx hardhat compile
npx hardhat test

# Start a local JSON-RPC node in a dedicated terminal
npx hardhat node

# In a new terminal (after the node is running), deploy locally
npx hardhat run scripts/deploy.js --network localhost
```

2) Backend (optional) — FastAPI + Supabase (or local Postgres)

```bash
cd frontend_with_backend/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Create .env with SUPABASE_URL and SUPABASE_KEY (see README_SETUP.md)
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

3) Frontend — start Vite dev server

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (commonly `http://localhost:3000/` or `http://localhost:5173/`).

## One-line start (dev)

This helper starts the frontend and runs tests; it requires you to have the Hardhat node running in another terminal.

```bash
# from repo root
concurrently "cd frontend && npm run dev" "cd smart-contracts && npx hardhat test --watch"
```

Install `concurrently` globally or with `npm i -g concurrently`.

## Architecture

High-level components:

```
[Browser / Wallet] <--> [Frontend (Vite React)] <--> [Backend (FastAPI) optional] <--> [Supabase/Postgres]
                                                 \
                                                  --> [Blockchain RPC / Hardhat node]

sprint3: [Postgres] + [Redis] + [fraud-api] + [dashboard]
```

## Demo & tests

- Run e2e demo script (needs node, backend and frontend running):

```bash
bash demo.sh
```

- Smart contract tests:

```bash
cd smart-contracts
npx hardhat test
```

## Troubleshooting

- If Hardhat node port is busy, stop other dev nodes or change the port.
- Backend: ensure `SUPABASE_URL` and `SUPABASE_KEY` are present in `frontend_with_backend/backend/.env`.
- Sprint3: requires Docker + Docker Compose; run `cd sprint3 && docker compose up -d`.

## Contributing & License

- Please open issues or PRs against `main`.
- Add a `LICENSE` file if you plan to publish; MIT is a common choice for demos.

---

_If you want I can add badges for build pipelines, CI, or a screenshot/demo GIF — tell me which assets to include._

# NFT-TICKETING

A focused, demonstration NFT ticketing application combining a React frontend, an example Python backend, and Ethereum smart contracts. The project contains smart contract sources, a Vite React frontend, an optional backend for demo integrations, and a sprint3 data/security stack with deployment artifacts.

**Goals**

- Demonstrate NFT-based ticket minting, resale and scanning flows.
- Provide a developer-friendly local environment for testing smart contracts and the UI.
- Offer integration examples (Python backend, Supabase migration scripts) for extending into production.

**Quick links**

- Smart contracts: `smart-contracts/`
- Frontend (Vite + React): `frontend/`
- Backend (example): `frontend_with_backend/backend/`
- Sprint 3 data/security stack: `sprint3/`

## Table of Contents

- [NFT-TICKETING](#nft-ticketing)
  - [Quickstart (local)](#quickstart-local)
  - [One-line start (dev)](#one-line-start-dev)
  - [Architecture](#architecture)
  - [Demo \& tests](#demo--tests)
  - [Troubleshooting](#troubleshooting)
  - [Contributing \& License](#contributing--license)
- [NFT-TICKETING](#nft-ticketing-1)
  - [Table of Contents](#table-of-contents)
  - [High-level structure](#high-level-structure)
  - [Prerequisites](#prerequisites)
  - [Quickstart — Local developer flow](#quickstart--local-developer-flow)
  - [Demo scripts](#demo-scripts)
  - [Running tests](#running-tests)
  - [Notes and troubleshooting](#notes-and-troubleshooting)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

## High-level structure

- `smart-contracts/` — Solidity source (`contracts/`), tests, Hardhat config, deployment scripts.
- `frontend/` — Vite + React + TypeScript app and components.
- `frontend_with_backend/` — Older/alternate frontend and a Python backend example with Supabase wiring.
- `sprint3/` — Data science & security layer (Docker Compose, ML pipeline, fraud API, monitoring).
- `demo.sh`, `blockchain_demo.py` — End-to-end demo scripts for local testing.

## Prerequisites

- Node.js (recommended v16+ or v18+ for some dev tooling)
- npm (or yarn)
- Python 3.8+ (3.11+ recommended for sprint3)
- Docker (for `sprint3` or running Postgres/Redis locally)

Optional developer tools

- `jq` (for demo scripts output), `curl`.

## Quickstart — Local developer flow

1) Smart contracts — compile, test and run a local node

```bash
cd smart-contracts
npm install
npx hardhat compile
npx hardhat test

# Start a local JSON-RPC node in a dedicated terminal
npx hardhat node

# In a new terminal (after the node is running), deploy locally
npx hardhat run scripts/deploy.js --network localhost
```

2) Frontend — start the development server

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (commonly `http://localhost:3000/` or `http://localhost:5173/`).

3) Backend (example) — optional FastAPI backend (Supabase-backed)

```bash
cd frontend_with_backend/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Create a .env with SUPABASE_URL and SUPABASE_KEY (see README_SETUP.md)
uvicorn server:app --host 0.0.0.0 --port 8000
```

Notes: the backend expects Supabase credentials or a compatible PostgreSQL + REST setup. See `frontend_with_backend/backend/README_SETUP.md` for details.

4) Sprint3 stack (data/fraud/monitoring) — Docker Compose

The `sprint3/` directory contains a `docker-compose.yml` that brings up Postgres, Redis, a fraud API and a monitoring dashboard. To run:

```bash
cd sprint3
# You need Docker and Docker Compose (docker-compose or `docker compose` plugin)
docker compose up -d
```

If your environment doesn't support the `docker compose` plugin, install the standalone `docker-compose` or use `docker run` to start required services.

## Demo scripts

- `demo.sh` runs a sequence of checks and example API calls (wallet creation, venue/event creation, minting). It assumes the Hardhat node, backend, and frontend are running.
- `blockchain_demo.py` contains a Python-based scenario runner (see file header for usage).

Run the demo after starting the node, backend and frontend:

```bash
bash demo.sh
```

## Running tests

- Smart contract unit tests (Hardhat):

```bash
cd smart-contracts
npx hardhat test
```

- Frontend tests: see `frontend/package.json` for test scripts if present.
- Backend tests: if present under `frontend_with_backend/backend/`, use `pytest` inside the virtual environment.

## Notes and troubleshooting

- Hardhat local node: ensure only one node is running on port 8545. If you get address-in-use errors stop previous nodes.
- Backend Supabase errors: ensure `SUPABASE_URL` and `SUPABASE_KEY` are set in `frontend_with_backend/backend/.env`.
- Docker Compose: some environments require installing the `docker-compose` package or using `docker compose` (Docker plugin). If `docker compose` fails, install the recommended client for your OS.

## Contributing

- Open an issue with a short description of the change.
- Create a branch, add tests where appropriate, and send a PR to `main`.

## License

No license file is included. Add a `LICENSE` if you intend to publish under an open-source license.

## Contact

Open an issue or contact the repository owner for questions or environment-specific help.

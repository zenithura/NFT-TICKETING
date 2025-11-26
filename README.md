# NFT-TICKETING

> A demonstration NFT-based ticketing dApp combining a React frontend, an optional Python backend, and Ethereum smart contracts. This repository contains the frontend app, backend integration examples, smart contract sources and deployment/test scripts used for demos and integration testing.

## Key Features

- NFT-based tickets managed by a smart contract (`TicketManager.sol`).
- Frontend UI built with React + TypeScript (Vite).
- Example Python backend for integration and demos (Supabase migration scripts included).
- Hardhat-based smart contract development, tests and deployment scripts.
- Demo scripts and example integrations for local testing.

## Repository Structure

- `frontend/` — Primary React + TypeScript frontend (Vite). See `frontend/package.json`.
- `frontend_with_backend/` — Alternate frontend + Python backend example and legacy frontend.
  - `frontend_with_backend/backend/` — Python backend, DB migrations and helper scripts.
- `smart-contracts/` — Solidity contracts, Hardhat config, artifacts, deploy and tests.
- `demo.sh`, `blockchain_demo.py` — Demo scripts used to exercise parts of the system.
- `diagrams/` — Architecture and sequence diagrams.

Notable files:

- `smart-contracts/contracts/TicketManager.sol` — Ticket management contract.
- `frontend/src` and `frontend/components` — UI and React components.
- `frontend_with_backend/backend/README_SETUP.md` — Backend setup instructions.

## Prerequisites

- Node.js (recommended v16+)
- npm or yarn
- Python 3.8+ (for the Python backend and demo scripts)
- Docker (optional, only if you prefer containerized DB or Supabase emulator)

For smart contract work:

- Hardhat (installed via `npm install` in `smart-contracts/`)

## Quickstart (local development)

1) Smart contracts (compile & test)

```
cd smart-contracts
npm install
npx hardhat compile
npx hardhat test
```

To run a local Hardhat node and deploy locally:

```
npx hardhat node
# in another terminal
node scripts/deploy.js
```

2) Frontend (Vite + React)

```
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (usually `http://localhost:5173`) to view the app.

3) Python backend (optional)

The example backend lives in `frontend_with_backend/backend` and provides helpers for DB setup and integrations.

```
cd frontend_with_backend/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Follow instructions in README_SETUP.md to configure database/Supabase
python server.py
```

4) Demo scripts

- `demo.sh` and `blockchain_demo.py` are convenience scripts used to show flows end-to-end. Review them before running.

## Development Flow

- Start a local blockchain (`npx hardhat node`).
- Deploy contracts (`node scripts/deploy.js`).
- Start backend (if used) and frontend.
- Use the frontend to mint/transfer/scan tickets, or run the demo scripts.

## Tests

- Smart contract unit tests: run `npx hardhat test` in `smart-contracts/`.
- Frontend: see `frontend/package.json` for available test scripts (if present).
- Integration/test harness: `frontend_with_backend/test_integration.py` and `frontend_with_backend/backend/test_integration` (if any).

## Notes & Pointers

- The `smart-contracts/artifacts` folder contains compiled outputs used in demos.
- `frontend/metadata.json` and `frontend/components` include UI metadata and sample components for the ticket display.
- `frontend_with_backend/backend/init_supabase_tables.sql` and other SQL files contain example DB schema and seed data for demo purposes.

## Contributing

If you'd like to contribute:

- Open an issue describing the feature or bug
- Send a PR against `main` with tests and a short description

## License

This repository does not include a license file. Add a `LICENSE` if you plan to publish or share the project publicly.

## Contact

For questions about this workspace contact the repo owner or open an issue in this repository.

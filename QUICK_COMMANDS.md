# Quick Commands Reference

## From Root Directory (`/NFT-TICKETING`)

### Frontend Commands
```bash
npm run dev              # Start frontend dev server (port 5173)
npm run dev:admin        # Start admin panel dev server (port 4201)
npm run build            # Build frontend for production
npm run build:perf       # Build with maximum performance optimizations
npm run build:admin      # Build admin panel
npm run build:analyze    # Build with bundle analysis
npm run preview          # Preview production build
npm run preview:admin    # Preview admin build
```

### Backend Commands
```bash
npm run backend:dev      # Start backend dev server (port 8000)
npm run backend:start    # Start backend using start script
```

### Testing & Performance
```bash
npm run test             # Run frontend tests
npm run test:e2e         # Run E2E tests
npm run perf:baseline    # Performance baseline
npm run perf:lighthouse  # Lighthouse performance audit
```

### Installation
```bash
npm run install:all      # Install frontend + backend dependencies
npm run install:frontend # Install only frontend dependencies
npm run install:backend  # Install only backend dependencies
```

## From Frontend Directory (`/frontend`)

All the same commands work directly:
```bash
cd frontend
npm run dev
npm run build:perf
# etc.
```

## From Backend Directory (`/backend`)

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
# or
./start_backend.sh
```

## Common Workflows

### Development
```bash
# Terminal 1: Backend
npm run backend:dev

# Terminal 2: Frontend
npm run dev

# Terminal 3: Admin Panel (optional)
npm run dev:admin
```

### Production Build
```bash
# Maximum performance build
npm run build:perf

# Preview build
npm run preview
```

### Performance Testing
```bash
# Build with optimizations
npm run build:perf

# Preview
npm run preview

# Run Lighthouse (in another terminal)
npx lighthouse http://localhost:4173 --view
```


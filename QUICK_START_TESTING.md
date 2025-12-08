# Quick Start: Full-Stack Testing & Monitoring

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Run Tests

**Backend Tests:**
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

**Frontend Tests:**
```bash
cd frontend
npm run e2e:headless
```

**All Tests:**
```bash
./run_all_tests.sh
```

### 3. Start Monitoring

```bash
./start_monitoring.sh
```

Access:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

### 4. Configure Sentry (Optional)

Add to `.env` files:

**Frontend** (`frontend/.env`):
```env
VITE_SENTRY_DSN=your-frontend-dsn
```

**Backend** (`backend/.env`):
```env
SENTRY_DSN=your-backend-dsn
```

## ✅ Test Coverage

- ✅ 13 Frontend E2E tests (all pages/components)
- ✅ 8 Backend test suites (all API endpoints)
- ✅ Full-stack integration tests
- ✅ Automated CI/CD testing

## 📊 Monitoring

- ✅ Real-time error tracking (Sentry)
- ✅ Metrics collection (Prometheus)
- ✅ Visual dashboards (Grafana)
- ✅ Automated alerting

## 🎯 Next Steps

1. Run `./run_all_tests.sh` to verify everything works
2. Access Grafana to view dashboards
3. Configure Sentry DSNs for error tracking
4. Push to GitHub to trigger CI/CD tests

See `FULLSTACK_TESTING_MONITORING.md` for detailed documentation.


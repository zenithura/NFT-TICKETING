# Performance Optimization Quick Start Guide

This guide explains how to run performance analysis and optimization for the NFT-TICKETING project.

## Prerequisites

```bash
# Frontend dependencies
cd frontend
npm install

# Backend dependencies (if testing backend)
cd ../backend
pip install -r requirements.txt
```

## Running Performance Analysis

### 1. Baseline Analysis

```bash
# Generate baseline performance reports
cd frontend
npm run build:perf
npm run perf:baseline
```

This generates:
- `perf/baseline/bundle.html` - Bundle size analysis
- `perf/baseline/js_css_coverage.json` - Unused code analysis
- `perf/lighthouse/*.json` - Lighthouse reports (if dev server running)

### 2. Coverage Analysis (Requires Dev Server)

```bash
# Terminal 1: Start dev server
cd frontend
npm run dev

# Terminal 2: Run coverage analysis
npm run perf:coverage
```

### 3. Lighthouse Analysis

```bash
# Terminal 1: Start dev server
cd frontend
npm run dev

# Terminal 2: Run Lighthouse CI
npm run perf:lighthouse
```

### 4. Backend Performance Tests

```bash
# Terminal 1: Start backend server
cd backend
python -m uvicorn main:app --reload

# Terminal 2: Run backend perf tests
cd frontend  # Scripts are in root
npm run perf:backend
```

### 5. Automated Scan and Fix

```bash
cd frontend
npm run perf:scan
```

This script:
- ✅ Applies low-risk fixes (lazy loading, script attributes)
- 📝 Generates suggestions for high-risk changes
- 📊 Saves results to `perf/auto_fixes.json` and `perf/suggestions/`

## Image Optimization

```bash
cd frontend
npm run optimize-images
```

Generates optimized images in `public/optimized/`:
- WebP versions
- Responsive sizes (320w, 640w, 1024w, 2048w)
- Optimized original format

## Build for Performance Analysis

```bash
cd frontend
npm run build:perf
```

Creates optimized build with bundle analyzer:
- Output: `dist_performance/`
- Bundle analysis: `dist_performance/bundle.html`

## CI/CD Integration

Performance tests run automatically on:
- Pull requests to `main`
- Pushes to `main`
- Manual workflow dispatch

**Workflow**: `.github/workflows/perf.yml`

The workflow:
1. Builds frontend with performance analysis
2. Runs Lighthouse CI
3. Runs Puppeteer coverage
4. Tests backend endpoints
5. Uploads artifacts
6. Comments on PRs with results

## Performance Targets

### Frontend
- **Lighthouse Performance**: 70+
- **LCP**: < 2500ms
- **FID**: < 100ms
- **CLS**: < 0.1
- **JS Bundle**: < 3MB total, < 300KB initial
- **CSS**: < 200KB total

### Backend
- **API Response Time (p95)**: < 200ms
- **Database Query Time (p95)**: < 50ms
- **Cache Hit Rate**: > 80%

## Viewing Reports

### Bundle Analysis
Open `dist_performance/bundle.html` in a browser for interactive bundle visualization.

### Lighthouse Reports
Lighthouse reports are saved to `perf/lighthouse/` as JSON files.

### Coverage Reports
Coverage analysis saved to `perf/baseline/js_css_coverage.json` or `perf/after/js_css_coverage.json`.

## Optimization Plans

See detailed plans in `perf/plan/`:
- `bundling_plan.md` - Code splitting strategy
- `lib_replacements.md` - Heavy library analysis
- `backend_optimizations.md` - Backend performance improvements
- `image_optimizations.md` - Image optimization strategy
- `css_optimizations.md` - CSS optimization approach

## Troubleshooting

### Bundle Analysis Not Generated
```bash
# Ensure PERF_MODE is set
PERF_MODE=true npm run build
```

### Coverage Analysis Fails
- Ensure dev server is running on `http://localhost:5173`
- Check Puppeteer installation: `npm install puppeteer`

### Lighthouse CI Fails
- Ensure dev server is running
- Check Lighthouse CI config: `.lighthouserc.js`
- Verify URLs are accessible

### Backend Tests Fail
- Ensure backend is running on `http://localhost:8000`
- Check backend health: `curl http://localhost:8000/health`

## Next Steps

1. Run baseline analysis: `npm run perf:baseline`
2. Review `perf/plan/` documents
3. Apply automated fixes: `npm run perf:scan`
4. Review suggestions in `perf/suggestions/`
5. Implement manual optimizations
6. Run after analysis and compare results
7. Review `perf/REPORT_TEMPLATE.md` for metrics comparison

## Support

For questions or issues:
1. Check optimization plans in `perf/plan/`
2. Review CI/CD logs in GitHub Actions
3. Examine artifacts uploaded by CI


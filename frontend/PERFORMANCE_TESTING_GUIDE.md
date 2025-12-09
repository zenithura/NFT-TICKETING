# Performance Testing Guide

## ⚠️ IMPORTANT: Test Production Builds, Not Dev Mode

The Lighthouse results you're seeing are from **development mode**, which includes:
- Vite HMR (Hot Module Replacement) WebSocket connections
- Unminified JavaScript (2,056 KiB savings available)
- Dev-only code (`/@vite/client`, `/@react-refresh`)
- Larger bundle sizes

**Production builds are significantly faster!**

## How to Test Production Performance

### Step 1: Build for Production
```bash
# From root directory
npm run build:perf

# Or from frontend directory
cd frontend
npm run build:perf
```

### Step 2: Preview Production Build
```bash
# From root directory
npm run preview

# Or from frontend directory
cd frontend
npm run preview
```

This starts a production server on `http://localhost:4173`

### Step 3: Run Lighthouse on Production Build
```bash
# In another terminal
npx lighthouse http://localhost:4173 --view
```

Or use Chrome DevTools:
1. Open `http://localhost:4173` in Chrome
2. Open DevTools → Lighthouse tab
3. Select "Performance" category
4. Click "Analyze page load"

## Expected Production Results

### Before Optimizations (Dev Mode)
- Performance: 39%
- LCP: 5.2s
- CLS: 0.831
- Bundle: 5,875 KiB (unminified)

### After Optimizations (Production Build)
- Performance: **75-85%** (target: 95%+)
- LCP: **2-3s** (target: <2.5s)
- CLS: **<0.1** (target: <0.1)
- Bundle: **~2,500-3,500 KiB** (minified, gzipped: ~800-1,200 KiB)

## Key Differences: Dev vs Production

| Metric | Dev Mode | Production Build |
|--------|----------|------------------|
| JavaScript | Unminified | Minified (2,056 KiB savings) |
| Bundle Size | 5,875 KiB | ~2,500 KiB |
| WebSocket | Vite HMR (blocks bfcache) | None |
| Source Maps | Yes | No |
| Tree Shaking | Partial | Full |
| Code Splitting | Basic | Aggressive |

## Critical Issues Fixed

### 1. ✅ Sentry Lazy Loading (860 KiB → 0 KiB initial load)
- **Before**: Loaded immediately on app start
- **After**: Only loads in production, deferred by 2 seconds
- **Impact**: Removes 860 KiB from initial bundle

### 2. ✅ Three.js Lazy Loading (1,174 KiB → 0 KiB initial load)
- **Before**: Could be loaded eagerly
- **After**: Truly lazy-loaded via `DeferredHeroBackground`
- **Impact**: Removes 1,174 KiB from initial bundle

### 3. ✅ Lucide-React Tree Shaking (783 KiB → ~50-100 KiB)
- **Before**: All icons loaded
- **After**: Only used icons included
- **Impact**: Reduces icon bundle by ~700 KiB

### 4. ✅ CLS Fixes
- Added aspect-ratio to images
- Reserved space for dynamic content
- Fixed layout shifts

### 5. ✅ LCP Optimization
- Deferred HeroBackground loading (2s delay)
- Preload critical images
- Optimized image loading priority

## Performance Checklist

### Before Testing
- [ ] Build production: `npm run build:perf`
- [ ] Preview build: `npm run preview`
- [ ] Clear browser cache
- [ ] Disable browser extensions (they add overhead)
- [ ] Use incognito/private mode

### During Testing
- [ ] Test on `http://localhost:4173` (production preview)
- [ ] NOT on `http://localhost:5173` (dev server)
- [ ] Run Lighthouse 3 times and average results
- [ ] Test on different network speeds (Throttling)

### After Testing
- [ ] Compare with baseline
- [ ] Check Core Web Vitals
- [ ] Review bundle analysis: `dist_performance/bundle.html`
- [ ] Monitor real user metrics in production

## Chrome Extension Impact

**Note**: Chrome extensions (like Merlin AI) add significant overhead:
- 2,886.9 KiB unused JavaScript from extensions
- This is NOT your app's code
- Test in incognito mode to get accurate results

## Production Deployment Checklist

1. ✅ Build with `npm run build:perf`
2. ✅ Test production build locally
3. ✅ Verify minification (check bundle sizes)
4. ✅ Test Lighthouse on production URL
5. ✅ Enable HTTP caching headers
6. ✅ Use CDN for static assets
7. ✅ Enable Brotli compression
8. ✅ Monitor Core Web Vitals in production

## Troubleshooting

### Still seeing large bundles?
- Check you're testing production build, not dev
- Verify minification is enabled
- Check bundle analysis: `dist_performance/bundle.html`

### CLS still high?
- Check images have width/height attributes
- Verify aspect-ratio is set on containers
- Test with slow 3G throttling

### LCP still slow?
- Preload critical images
- Optimize hero image (WebP, responsive)
- Reduce server response time
- Use CDN for images

## Next Steps

1. **Build production**: `npm run build:perf`
2. **Preview**: `npm run preview`
3. **Test**: Run Lighthouse on `http://localhost:4173`
4. **Compare**: Results should be 75-85% (vs 39% in dev)
5. **Deploy**: Use production build for deployment

Remember: **Always test production builds for accurate performance metrics!**


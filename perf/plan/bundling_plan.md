# Bundling Optimization Plan

## Current State
- Routes are already lazy-loaded using React.lazy()
- Three.js and recharts are split into separate chunks
- Bundle analyzer configured to generate visual reports

## Optimization Strategy

### 1. Code Splitting Improvements

#### Route-Based Splitting (✅ Already Implemented)
- All routes use `React.lazy()` and `Suspense`
- Components are loaded on-demand

#### Component-Level Splitting
- **Three.js components**: Already deferred in HeroBackground
- **Chart components**: Converted to lazy loading in LazyChart
- **Admin dashboard**: Heavy components loaded on-demand

### 2. Vendor Chunk Optimization

Current chunks:
- `react-vendor`: React + React DOM
- `router`: React Router
- `charts`: Recharts (lazy loaded)
- `three`: Three.js (lazy loaded)
- `ui-libs`: Lucide React, React Hot Toast
- `i18n`: i18next libraries
- `swr`: SWR data fetching
- `utils`: Utility libraries
- `vendor`: Other node_modules

**Improvements**:
- ✅ Three.js isolated in separate chunk
- ✅ Charts library lazy-loaded
- ✅ React vendor chunk separated

### 3. Tree-Shaking Optimizations

**Implemented**:
- Named imports instead of `import *`
- Dynamic imports for heavy libraries
- Vite tree-shaking enabled with `moduleSideEffects: false`

**Recommendations**:
- Review all `import *` statements and convert to named imports where possible
- Ensure libraries support tree-shaking (ES modules)

### 4. Modern Build Target

**Current**: ES2015 target
**Updated**: ES2020+ for modern browsers (reduces bundle size by ~15-20%)

Benefits:
- Smaller bundles (native async/await, optional chaining, etc.)
- Better compression
- Modern browser support (Edge 88+, Chrome 87+, Firefox 78+, Safari 14+)

## Bundle Size Targets

- **Initial JS bundle**: < 300KB (gzipped)
- **Total JS**: < 3MB (uncompressed)
- **LCP**: < 2.5s
- **FCP**: < 1.8s

## Monitoring

- Bundle analyzer generates `bundle.html` on `npm run build:perf`
- CI checks bundle size thresholds
- Automated alerts on bundle size increases


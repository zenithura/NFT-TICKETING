# Heavy Library Replacement Analysis

## Libraries Analyzed

### 1. Three.js (0.162.0)
- **Current Size**: ~600KB (uncompressed), ~180KB (gzipped)
- **Usage**: HeroBackground, NFTCoinAnimation components
- **Status**: ✅ Optimized
  - Lazy-loaded with React.lazy()
  - Deferred loading after initial render
  - WebGL fallback for unsupported browsers
- **Replacement Risk**: High
- **Recommendation**: Keep - already optimized, replacement would require significant refactoring

### 2. Recharts (2.12.2)
- **Current Size**: ~500KB (uncompressed), ~150KB (gzipped)
- **Usage**: Dashboard charts, admin analytics
- **Status**: ✅ Optimized
  - Converted to lazy loading in LazyChart component
  - Only loaded when charts are displayed
- **Replacement Options**:
  - **lightweight-charts**: ~150KB (uncompressed) - TradingView's lightweight library
  - **Chart.js**: ~200KB (uncompressed) - Popular alternative
  - **Victory**: Similar size to Recharts
- **Replacement Risk**: Medium
- **Recommendation**: Keep for now - lazy loading solves the performance issue. Consider lightweight-charts if charts become more central to the app.

### 3. i18next (i18next + react-i18next)
- **Current Size**: ~150KB (uncompressed), ~50KB (gzipped)
- **Usage**: Internationalization (translations)
- **Status**: ⚠️ Could be optimized
- **Optimization Options**:
  - Lazy-load translations per language
  - Split translation files by route
- **Replacement Risk**: Low
- **Recommendation**: Keep - essential for i18n, optimize by lazy-loading translations

### 4. Sentry (@sentry/react)
- **Current Size**: ~200KB (uncompressed), ~70KB (gzipped)
- **Usage**: Error tracking and monitoring
- **Status**: ✅ Optimized
  - Initialized in separate file
  - Can be disabled in development
- **Replacement Risk**: High (critical for production monitoring)
- **Recommendation**: Keep - essential for production error tracking

### 5. SWR (2.3.7)
- **Current Size**: ~20KB (uncompressed), ~10KB (gzipped)
- **Usage**: Data fetching and caching
- **Status**: ✅ Acceptable
- **Replacement Risk**: Low
- **Recommendation**: Keep - lightweight and essential for data fetching

## Summary

### Low-Risk Replacements
- None identified - all heavy libraries are either essential or already optimized

### Medium-Risk Optimizations
- **Recharts**: Could be replaced with lightweight-charts if charts become more important
- **i18next**: Optimize by lazy-loading translations per language

### High-Risk (Keep as-is)
- **Three.js**: Already optimized, replacement too risky
- **Sentry**: Essential for production monitoring
- **React/React DOM**: Core framework

## Action Items

1. ✅ Implement lazy loading for Three.js components
2. ✅ Convert Recharts to lazy loading
3. ⚠️ Consider lazy-loading i18next translations
4. ⚠️ Monitor bundle size in CI/CD


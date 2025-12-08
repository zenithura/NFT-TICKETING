# CSS Optimization Plan

## Current State
- Using Tailwind CSS v4
- PostCSS configured
- CSS code splitting enabled in Vite

## Optimization Strategy

### 1. Tailwind Purge/Content Configuration

**Status**: ✅ Already optimized
- Tailwind v4 uses JIT mode by default
- Content paths should be configured in `tailwind.config.js`

**Ensure content paths are correct**:
```js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
  ],
}
```

### 2. CSS Code Splitting

**Status**: ✅ Enabled in Vite
```js
build: {
  cssCodeSplit: true, // Split CSS per route/component
}
```

**Benefits**:
- CSS loaded per route, not all at once
- Smaller initial CSS bundle
- Faster FCP

### 3. Unused CSS Removal

**Tool**: PurgeCSS (integrated with Tailwind)
**Status**: ✅ Automatic with Tailwind JIT

**Manual check**:
- Run bundle analyzer to see CSS sizes
- Use Puppeteer coverage to identify unused CSS

### 4. CSS Minification

**Status**: ✅ Enabled in Vite production build
- Automatic minification in production
- PostCSS optimizations applied

### 5. Critical CSS

**Consideration**: Inline critical CSS for above-the-fold content

**Implementation** (if needed):
```html
<style>
  /* Critical CSS inline */
</style>
<link rel="preload" href="/assets/css/index.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
```

## Monitoring

- CSS bundle size tracked in bundle analyzer
- Coverage reports show unused CSS percentage
- CI/CD checks for CSS size increases

## Targets

- **Initial CSS**: < 50KB (gzipped)
- **Total CSS**: < 200KB (gzipped)
- **Unused CSS**: < 30%

## Current Status

✅ Tailwind JIT mode (automatic purging)
✅ CSS code splitting enabled
✅ Minification enabled in production
✅ PostCSS optimizations

## Action Items

1. ✅ Verify Tailwind content paths
2. ⚠️ Monitor CSS bundle size in CI
3. ⚠️ Review unused CSS in coverage reports


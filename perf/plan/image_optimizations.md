# Image Optimization Plan

## Current State
- Images stored in `public/` directory
- No optimization pipeline
- No responsive image sizes
- No WebP format support

## Optimization Strategy

### 1. Build-Time Image Optimization

**Tool**: Sharp (Node.js image processing library)
**Script**: `scripts/optimize-images.js`

**Process**:
1. Scan `public/` directory for images
2. Generate responsive sizes: 320w, 640w, 1024w, 2048w
3. Generate WebP versions for each size
4. Generate optimized original format versions
5. Save to `public/optimized/`

### 2. Responsive Images

**Implementation**: Use `<picture>` element with `srcset`

```tsx
<picture>
  <source
    srcSet="/optimized/image-320w.webp 320w, /optimized/image-640w.webp 640w, /optimized/image-1024w.webp 1024w"
    type="image/webp"
    sizes="(max-width: 640px) 320px, (max-width: 1024px) 640px, 1024px"
  />
  <img
    srcSet="/optimized/image-320w.jpg 320w, /optimized/image-640w.jpg 640w, /optimized/image-1024w.jpg 1024w"
    src="/optimized/image-1024w.jpg"
    alt="Description"
    loading="lazy"
  />
</picture>
```

### 3. LazyImage Component

**Component**: `components/LazyImage.tsx`

**Features**:
- IntersectionObserver-based lazy loading
- WebP with fallback
- Responsive srcset
- Placeholder/skeleton while loading
- Native `loading="lazy"` attribute

### 4. Optimization Settings

- **WebP Quality**: 85% (good balance of size/quality)
- **JPEG Quality**: 85% with mozjpeg optimizations
- **PNG**: Lossless compression
- **Sizes**: 320w, 640w, 1024w, 2048w

### 5. Usage Guidelines

**Replace existing images**:
```tsx
// Before
<img src="/event-image.jpg" alt="Event" />

// After
<LazyImage
  src="/optimized/event-image-1024w.jpg"
  webpSrc="/optimized/event-image.webp"
  srcSet="/optimized/event-image-320w.jpg 320w, /optimized/event-image-640w.jpg 640w, /optimized/event-image-1024w.jpg 1024w"
  webpSrcSet="/optimized/event-image-320w.webp 320w, /optimized/event-image-640w.webp 640w, /optimized/event-image-1024w.webp 1024w"
  sizes="(max-width: 640px) 320px, (max-width: 1024px) 640px, 1024px"
  alt="Event"
  dataCy="event-image"
/>
```

### 6. CI Integration

**Script**: `npm run optimize-images`
**When**: Before build in CI/CD
**Output**: Optimized images in `public/optimized/`

## Expected Savings

- **File Size Reduction**: 60-80% (WebP vs original)
- **Page Load Improvement**: 20-40% faster LCP
- **Bandwidth Savings**: Significant for users on slow connections

## Next Steps

1. ✅ Create optimization script
2. ✅ Create LazyImage component
3. ⚠️ Run optimization on existing images
4. ⚠️ Update image references to use LazyImage
5. ⚠️ Add to CI/CD pipeline


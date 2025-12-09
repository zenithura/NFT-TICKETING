/**
 * Image utility functions for optimized image delivery
 */

/**
 * Generate optimized placeholder image URL
 * Uses a lightweight SVG data URI instead of external service
 */
export function getPlaceholderImage(width: number = 800, height: number = 400): string {
  // Use SVG data URI for instant loading, no network request
  const svg = `
    <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#F7931A;stop-opacity:0.2" />
          <stop offset="100%" style="stop-color:#D97706;stop-opacity:0.1" />
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#grad)"/>
      <text x="50%" y="50%" font-family="Inter, sans-serif" font-size="24" fill="#F7931A" text-anchor="middle" dominant-baseline="middle" opacity="0.5">NFTix Event</text>
    </svg>
  `.trim();
  
  return `data:image/svg+xml;base64,${btoa(svg)}`;
}

/**
 * Generate responsive image srcset
 */
export function generateSrcSet(baseUrl: string, widths: number[] = [400, 800, 1200]): string {
  return widths.map(width => `${baseUrl}?w=${width} ${width}w`).join(', ');
}

/**
 * Generate sizes attribute for responsive images
 */
export function generateSizes(breakpoints: { [key: string]: string } = {}): string {
  const defaultSizes = {
    '(max-width: 640px)': '100vw',
    '(max-width: 1024px)': '50vw',
    'default': '33vw'
  };
  
  const sizes = { ...defaultSizes, ...breakpoints };
  return Object.entries(sizes)
    .filter(([key]) => key !== 'default')
    .map(([key, value]) => `${key} ${value}`)
    .concat(sizes.default ? [sizes.default] : [])
    .join(', ');
}

/**
 * Convert image URL to WebP if supported
 */
export function getWebPUrl(url: string): string {
  if (url.startsWith('data:') || url.includes('.svg')) {
    return url; // Don't convert data URIs or SVGs
  }
  
  // If URL already has query params, append, otherwise add
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}format=webp`;
}



/**
 * LCP (Largest Contentful Paint) Optimizer
 * Optimizes the largest contentful element for better LCP scores
 */

import { useEffect } from 'react';

export const LCPOptimizer: React.FC = () => {
  useEffect(() => {
    // Preload critical LCP images
    const preloadLCPImages = () => {
      // Find the first image in the viewport (likely LCP element)
      const images = document.querySelectorAll<HTMLImageElement>('img[loading="eager"], img[fetchpriority="high"]');
      
      images.forEach((img, index) => {
        if (index === 0 && img.src && !img.complete) {
          // Preload the first critical image
          const link = document.createElement('link');
          link.rel = 'preload';
          link.as = 'image';
          link.href = img.src;
          if (img.srcset) {
            link.setAttribute('imagesrcset', img.srcset);
          }
          if (img.sizes) {
            link.setAttribute('imagesizes', img.sizes);
          }
          link.fetchPriority = 'high';
          document.head.appendChild(link);
        }
      });
    };

    // Optimize font loading for LCP
    const optimizeFonts = () => {
      // Ensure fonts are loaded with font-display: swap
      const fontLinks = document.querySelectorAll<HTMLLinkElement>('link[rel="stylesheet"][href*="fonts.googleapis.com"]');
      fontLinks.forEach(link => {
        if (!link.media || link.media === 'all') {
          link.media = 'print';
          link.onload = () => {
            link.media = 'all';
          };
        }
      });
    };

    // Reserve space for LCP element to prevent CLS
    const reserveLCPSpace = () => {
      const lcpCandidates = document.querySelectorAll('[data-lcp-candidate]');
      lcpCandidates.forEach((element) => {
        const htmlElement = element as HTMLElement;
        if (!htmlElement.style.minHeight) {
          // Set min-height based on aspect ratio or content
          const aspectRatio = htmlElement.dataset.aspectRatio || '16/9';
          const [width, height] = aspectRatio.split('/').map(Number);
          const minHeight = (htmlElement.offsetWidth / width) * height;
          htmlElement.style.minHeight = `${minHeight}px`;
        }
      });
    };

    // Run optimizations
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        preloadLCPImages();
        optimizeFonts();
        reserveLCPSpace();
      });
    } else {
      preloadLCPImages();
      optimizeFonts();
      reserveLCPSpace();
    }

    // Re-check after images load
    const images = document.querySelectorAll('img');
    images.forEach((img) => {
      if (img.complete) {
        reserveLCPSpace();
      } else {
        img.addEventListener('load', reserveLCPSpace, { once: true });
      }
    });
  }, []);

  return null;
};


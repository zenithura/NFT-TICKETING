/**
 * Image Optimizer Component
 * Optimizes image loading for better LCP and performance
 */

import { useEffect } from 'react';

export const ImageOptimizer: React.FC = () => {
  useEffect(() => {
    // Preload critical images
    const preloadCriticalImages = () => {
      const criticalImages = document.querySelectorAll<HTMLImageElement>('img[data-critical="true"]');
      criticalImages.forEach((img) => {
        if (img.src && !img.complete) {
          const link = document.createElement('link');
          link.rel = 'preload';
          link.as = 'image';
          link.href = img.src;
          if (img.srcset) {
            link.setAttribute('imagesrcset', img.srcset);
          }
          document.head.appendChild(link);
        }
      });
    };

    // Lazy load images with Intersection Observer
    const setupLazyLoading = () => {
      const images = document.querySelectorAll<HTMLImageElement>('img[loading="lazy"]');
      
      if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLImageElement;
              if (img.dataset.src) {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
              }
              imageObserver.unobserve(img);
            }
          });
        }, {
          rootMargin: '50px',
        });

        images.forEach((img) => {
          if (img.dataset.src) {
            imageObserver.observe(img);
          }
        });
      }
    };

    // Optimize image loading priority
    const optimizeImagePriority = () => {
      const viewportHeight = window.innerHeight;
      const images = document.querySelectorAll<HTMLImageElement>('img');
      
      images.forEach((img) => {
        const rect = img.getBoundingClientRect();
        const isAboveFold = rect.top < viewportHeight;
        
        if (isAboveFold && img.loading !== 'eager') {
          img.loading = 'eager';
          img.fetchPriority = 'high';
        } else if (!isAboveFold && img.loading !== 'lazy') {
          img.loading = 'lazy';
          img.fetchPriority = 'low';
        }
      });
    };

    // Run optimizations
    preloadCriticalImages();
    setupLazyLoading();
    optimizeImagePriority();

    // Re-optimize on scroll (debounced)
    let scrollTimeout: NodeJS.Timeout;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(optimizeImagePriority, 100);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return null;
};


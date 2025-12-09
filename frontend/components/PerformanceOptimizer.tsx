/**
 * Performance Optimizer Component
 * Handles bfcache, layout shifts, and performance optimizations
 */

import { useEffect } from 'react';

export const PerformanceOptimizer: React.FC = () => {
  useEffect(() => {
    // Fix back/forward cache (bfcache) issues
    // Ensure pages can be restored from bfcache
    const handlePageShow = (e: PageTransitionEvent) => {
      if (e.persisted) {
        // Page was restored from bfcache
        // Re-initialize any necessary state
        window.scrollTo(0, 0);
      }
    };

    window.addEventListener('pageshow', handlePageShow);

    // Prevent layout shifts by reserving space for dynamic content
    const reserveSpaceForDynamicContent = () => {
      // Add min-height to containers that might cause CLS
      const containers = document.querySelectorAll('[data-dynamic-content]');
      containers.forEach((container) => {
        if (!(container as HTMLElement).style.minHeight) {
          (container as HTMLElement).style.minHeight = '200px';
        }
      });
    };

    // Run after initial render
    setTimeout(reserveSpaceForDynamicContent, 100);

    // Optimize long tasks by breaking them up
    if ('scheduler' in window && 'postTask' in (window as any).scheduler) {
      // Use scheduler.postTask for non-critical work
      const scheduler = (window as any).scheduler;
      scheduler.postTask(() => {
        // Defer non-critical initialization
      }, { priority: 'background' });
    }

    // Preload critical resources
    const preloadCriticalResources = () => {
      const criticalImages = document.querySelectorAll('img[data-critical]');
      criticalImages.forEach((img) => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        link.href = (img as HTMLImageElement).src;
        document.head.appendChild(link);
      });
    };

    preloadCriticalResources();

    return () => {
      window.removeEventListener('pageshow', handlePageShow);
    };
  }, []);

  return null;
};


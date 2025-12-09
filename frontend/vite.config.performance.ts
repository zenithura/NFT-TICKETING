/**
 * Performance-optimized Vite configuration
 * Use this for production builds: vite build --config vite.config.performance.ts
 */

import { defineConfig } from './vite.config';

export default defineConfig({
  build: {
    // Maximum compression
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug', 'console.warn'],
        passes: 5,
        dead_code: true,
        unused: true,
        collapse_vars: true,
        reduce_vars: true,
      },
      mangle: {
        safari10: true,
        properties: {
          regex: /^_/,
        },
      },
      format: {
        comments: false,
      },
    },
    // Aggressive chunk splitting
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // React core
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react-core';
          }
          // Router
          if (id.includes('node_modules/react-router')) {
            return 'router';
          }
          // Heavy libraries - lazy load
          if (id.includes('node_modules/recharts')) return 'charts';
          if (id.includes('node_modules/three')) return 'three';
          if (id.includes('node_modules/@sentry')) return 'sentry';
          // Split by package for better caching
          if (id.includes('node_modules')) {
            const match = id.match(/node_modules\/(@?[^/]+)/);
            if (match) {
              return `vendor-${match[1].replace('@', '')}`;
            }
          }
        },
      },
    },
    chunkSizeWarningLimit: 200,
    cssMinify: true,
    sourcemap: false,
    assetsInlineLimit: 1024, // Even smaller inline limit
  },
});


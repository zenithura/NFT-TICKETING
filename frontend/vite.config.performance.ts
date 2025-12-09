/**
 * Performance-optimized Vite configuration
 * Use this for production builds: vite build --config vite.config.performance.ts
 */

import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  
  return {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      }
    },
    plugins: [react()],
    define: {
      'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
    },
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
      // Aggressive chunk splitting - prevent empty chunks
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            // React core
            if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
              return 'react-vendor';
            }
            // Router
            if (id.includes('node_modules/react-router')) {
              return 'router';
            }
            // Heavy libraries - lazy load
            if (id.includes('node_modules/recharts')) return 'charts';
            if (id.includes('node_modules/three')) return 'three';
            if (id.includes('node_modules/@sentry')) return 'sentry';
            // UI libraries
            if (id.includes('node_modules/lucide-react')) return 'icons';
            if (id.includes('node_modules/react-hot-toast')) return 'toast';
            // i18n
            if (id.includes('node_modules/i18next')) return 'i18n-core';
            if (id.includes('node_modules/react-i18next')) return 'i18n-react';
            // SWR
            if (id.includes('node_modules/swr')) return 'swr';
            // Utilities - group small packages
            if (id.includes('node_modules/clsx') || 
                id.includes('node_modules/tailwind-merge') ||
                id.includes('node_modules/dequal') ||
                id.includes('node_modules/fast-equals') ||
                id.includes('node_modules/tiny-invariant')) {
              return 'utils';
            }
            // D3 libraries - group together
            if (id.includes('node_modules/d3-')) {
              return 'd3';
            }
            // Group very small packages that create empty chunks
            const tinyPackages = ['babel', 'dom-helpers', 'hoist-non-react-statics', 
                                 'html-parse-stringify', 'localforage', 'void-elements',
                                 'internmap', 'use-sync-external-store', 'prop-types',
                                 'goober', 'eventemitter3', 'scheduler', 'victory-vendor'];
            if (id.includes('node_modules') && tinyPackages.some(pkg => id.includes(pkg))) {
              return 'vendor-tiny';
            }
            // Large packages get their own chunk
            if (id.includes('node_modules/lodash')) return 'vendor-lodash';
            if (id.includes('node_modules/decimal.js-light')) return 'vendor-decimal';
            if (id.includes('node_modules/remix-run')) return 'vendor-remix';
            // Other node_modules - group together
            if (id.includes('node_modules')) {
              return 'vendor-other';
            }
            // Don't create chunks for application code
            return null;
          },
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
        },
      },
      chunkSizeWarningLimit: 400, // Allow three.js and charts to be large (they're lazy loaded)
      cssMinify: true,
      cssCodeSplit: true,
      sourcemap: false,
      assetsInlineLimit: 2048,
      target: ['es2022', 'edge88', 'firefox78', 'chrome87', 'safari14'],
      treeshake: {
        moduleSideEffects: false,
        propertyReadSideEffects: false,
        tryCatchDeoptimization: false,
      },
    },
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-router-dom'],
    },
  };
});

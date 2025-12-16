import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const isPerfMode = process.env.PERF_MODE === 'true';
  
  return {
    server: {
      port: 5173,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          // Preserve cookies for admin authentication
          cookieDomainRewrite: '',
          cookiePathRewrite: '/',
        },
      },
    },
    plugins: [
      react(),
      // Bundle visualizer for performance analysis
      isPerfMode && visualizer({
        open: false,
        filename: 'dist_performance/bundle.html',
        gzipSize: true,
        brotliSize: true,
        template: 'treemap', // or 'sunburst', 'network'
      }),
    ].filter(Boolean),
    define: {
      'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      }
    },
    // Build optimizations for performance
    build: {
      // Always enable minification for better performance
      minify: mode === 'production' ? 'terser' : 'esbuild',
      terserOptions: mode === 'production' ? {
        compress: {
          drop_console: true, // Remove console.logs in production
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info', 'console.debug', 'console.warn'],
          passes: 3, // More passes for better compression
          dead_code: true,
          unused: true,
        },
        mangle: {
          safari10: true, // Fix Safari 10 issues
          properties: {
            regex: /^_/,
          },
        },
        format: {
          comments: false,
        },
      } : undefined,
      esbuild: {
        minifyIdentifiers: true,
        minifySyntax: true,
        minifyWhitespace: true,
        legalComments: 'none',
        treeShaking: true,
      },
      // Code splitting configuration
      rollupOptions: {
        output: {
          // Aggressive code splitting to reduce unused JavaScript
          manualChunks: (id) => {
            // React and core libraries (most critical)
            if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
              return 'react-vendor';
            }
            // Router (separate chunk)
            if (id.includes('node_modules/react-router')) {
              return 'router';
            }
            // Charts (heavy library - lazy load)
            if (id.includes('node_modules/recharts')) {
              return 'charts';
            }
            // Three.js (3D library - very heavy, lazy load)
            if (id.includes('node_modules/three')) {
              return 'three';
            }
            // UI libraries (split further)
            if (id.includes('node_modules/lucide-react')) {
              return 'icons';
            }
            if (id.includes('node_modules/react-hot-toast')) {
              return 'toast';
            }
            // i18n (split)
            if (id.includes('node_modules/i18next')) {
              return 'i18n-core';
            }
            if (id.includes('node_modules/react-i18next')) {
              return 'i18n-react';
            }
            // SWR (data fetching)
            if (id.includes('node_modules/swr')) {
              return 'swr';
            }
            // Utilities (small, can be inlined)
            if (id.includes('node_modules/clsx') || id.includes('node_modules/tailwind-merge')) {
              return 'utils';
            }
            // Sentry (monitoring - lazy load)
            if (id.includes('node_modules/@sentry')) {
              return 'sentry';
            }
            // Other node_modules - group small packages, split large ones
            if (id.includes('node_modules')) {
              // Extract package name for better splitting
              const match = id.match(/node_modules\/(@?[^/]+)/);
              if (match) {
                const packageName = match[1].replace('@', '');
                // Group small packages together
                if (['clsx', 'tailwind-merge', 'dequal', 'fast-equals', 'tiny-invariant'].includes(packageName)) {
                  return 'utils';
                }
                // Group very small packages that create empty chunks
                const tinyPackages = ['babel', 'dom-helpers', 'hoist-non-react-statics', 
                                     'html-parse-stringify', 'localforage', 'void-elements',
                                     'internmap', 'use-sync-external-store', 'prop-types',
                                     'goober', 'eventemitter3', 'scheduler', 'victory-vendor'];
                if (tinyPackages.some(pkg => packageName.includes(pkg))) {
                  return 'vendor-tiny';
                }
                // D3 libraries - group together
                if (packageName.startsWith('d3-')) {
                  return 'd3';
                }
                // Large packages get their own chunk
                if (packageName === 'lodash') return 'vendor-lodash';
                if (packageName === 'decimal.js-light') return 'vendor-decimal';
                if (packageName === 'remix-run') return 'vendor-remix';
                // Other packages grouped
                return 'vendor-other';
              }
              return 'vendor-other';
            }
          },
          // Optimize chunk file names
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
        },
      },
      // Chunk size warnings (reduce for better splitting)
      chunkSizeWarningLimit: 300,
      // Report chunk sizes
      reportCompressedSize: true,
      // Enable CSS code splitting and minification
      cssCodeSplit: true,
      cssMinify: mode === 'production',
      // Source maps for production (disable for better performance)
      sourcemap: false,
      // Asset optimization - inline smaller assets
      assetsInlineLimit: 2048, // Reduced from 4kb to 2kb
      // Target modern browsers for smaller bundles (ES2020 for better tree-shaking)
      target: ['es2022', 'edge88', 'firefox78', 'chrome87', 'safari14'],
      // Aggressive tree shaking
      treeshake: {
        moduleSideEffects: false,
        propertyReadSideEffects: false,
        tryCatchDeoptimization: false,
      },
    },
    // Optimize dependencies
    optimizeDeps: {
      include: [
        'react', 
        'react-dom', 
        'react-router-dom', 
        'recharts'
      ],
      exclude: [],
      // Ensure React is properly resolved for recharts
      esbuildOptions: {
        resolveExtensions: ['.tsx', '.ts', '.jsx', '.js'],
      },
    },
  };
});

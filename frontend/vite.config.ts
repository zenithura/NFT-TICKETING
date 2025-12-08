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
      // Enable minification (only in production)
      minify: mode === 'production' ? 'terser' : false,
      terserOptions: mode === 'production' ? {
        compress: {
          drop_console: true, // Remove console.logs in production
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info', 'console.debug'],
          passes: 2, // Multiple passes for better compression
        },
        mangle: {
          safari10: true, // Fix Safari 10 issues
        },
      } : undefined,
      // Code splitting configuration
      rollupOptions: {
        output: {
          // Manual chunks for better code splitting
          manualChunks: (id) => {
            // React and core libraries
            if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
              return 'react-vendor';
            }
            // Router
            if (id.includes('node_modules/react-router')) {
              return 'router';
            }
            // Charts (heavy library)
            if (id.includes('node_modules/recharts')) {
              return 'charts';
            }
            // Three.js (3D library - very heavy)
            if (id.includes('node_modules/three')) {
              return 'three';
            }
            // UI libraries
            if (id.includes('node_modules/lucide-react') || id.includes('node_modules/react-hot-toast')) {
              return 'ui-libs';
            }
            // i18n
            if (id.includes('node_modules/i18next') || id.includes('node_modules/react-i18next')) {
              return 'i18n';
            }
            // SWR
            if (id.includes('node_modules/swr')) {
              return 'swr';
            }
            // Utilities
            if (id.includes('node_modules/clsx') || id.includes('node_modules/tailwind-merge')) {
              return 'utils';
            }
            // Other node_modules
            if (id.includes('node_modules')) {
              return 'vendor';
            }
          },
          // Optimize chunk file names
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
        },
      },
      // Chunk size warnings (increase limit slightly for heavy 3D libraries)
      chunkSizeWarningLimit: 600,
      // Report chunk sizes
      reportCompressedSize: true,
      // Enable CSS code splitting
      cssCodeSplit: true,
      // Source maps for production (disable for better performance)
      sourcemap: false,
      // Asset optimization
      assetsInlineLimit: 4096, // Inline assets smaller than 4kb
      // Target modern browsers for smaller bundles (ES2020 for better tree-shaking)
      target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
      // Tree shaking
      treeshake: {
        moduleSideEffects: false,
      },
    },
    // Optimize dependencies
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-router-dom'],
    },
  };
});

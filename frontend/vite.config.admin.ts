import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';

// Custom plugin to use index.admin.html in dev mode
const adminHtmlPlugin = () => {
  return {
    name: 'admin-html-plugin',
    configureServer(server) {
      const adminHtmlPath = path.resolve(__dirname, 'index.admin.html');
      
      // Override the transformIndexHtml to use admin HTML
      const originalTransform = server.transformIndexHtml;
      server.transformIndexHtml = async (url, html, ctx) => {
        // Always use admin HTML instead of default index.html
        if (fs.existsSync(adminHtmlPath)) {
          const adminHtml = fs.readFileSync(adminHtmlPath, 'utf-8');
          // Apply Vite's transforms to the admin HTML
          if (originalTransform) {
            return originalTransform(url, adminHtml, ctx);
          }
          return adminHtml;
        }
        // Fallback
        if (originalTransform) {
          return originalTransform(url, html, ctx);
        }
        return html;
      };
    },
  };
};

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  
  return {
    root: '.',
    publicDir: 'public',
    server: {
      port: 4201,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          cookieDomainRewrite: '',
          cookiePathRewrite: '/',
        },
      },
    },
    plugins: [
      adminHtmlPlugin(),
      react({
        include: '**/*.{jsx,tsx}',
      }),
    ],
    define: {
      'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
      'process.env.ADMIN_PORT': JSON.stringify('4201'),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      }
    },
    build: {
      outDir: 'dist-admin',
      rollupOptions: {
        input: path.resolve(__dirname, 'index.admin.html'),
        output: {
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
        },
      },
      minify: mode === 'production' ? 'terser' : false,
      terserOptions: mode === 'production' ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info', 'console.debug'],
          passes: 2,
        },
        mangle: {
          safari10: true,
        },
      } : undefined,
      chunkSizeWarningLimit: 600,
      reportCompressedSize: true,
      cssCodeSplit: true,
      sourcemap: false,
      assetsInlineLimit: 4096,
      target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
      treeshake: {
        moduleSideEffects: false,
      },
    },
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-router-dom'],
    },
  };
});


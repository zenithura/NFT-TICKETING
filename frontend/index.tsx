// File header: Application entry point with i18n initialization.
// Initializes React application and internationalization support.

import React from 'react';
import ReactDOM from 'react-dom/client';
import './i18n'; // Initialize i18n synchronously - translations are small and needed immediately
// Lazy load Sentry to reduce initial bundle size (860 KiB savings)
// Only load in production or when explicitly needed
if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
  import('./lib/sentry').catch(() => {
    // Silently fail if Sentry can't be loaded
  });
}
import App from './App';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

// CRITICAL: Ensure gradient background persists after navigation and refresh
// Safeguard: Verify html, body, and #root are transparent to show gradient
// This works in harmony with CSS rules (doesn't override, just verifies)
const ensureGradientVisibility = () => {
  const html = document.documentElement;
  const body = document.body;
  
  // Ensure body is transparent (CSS should handle this, but verify)
  if (body.style.backgroundColor && body.style.backgroundColor !== 'transparent') {
    body.style.backgroundColor = 'transparent';
  }
  if (body.style.background && !body.style.background.includes('inherit') && !body.style.background.includes('transparent')) {
    body.style.background = 'inherit';
  }
  
  // Ensure root element is transparent
  if (rootElement) {
    if (rootElement.style.backgroundColor && rootElement.style.backgroundColor !== 'transparent') {
      rootElement.style.backgroundColor = 'transparent';
    }
    if (rootElement.style.background && !rootElement.style.background.includes('inherit') && !rootElement.style.background.includes('transparent')) {
      rootElement.style.background = 'inherit';
    }
  }
};

// Apply verification immediately and after CSS loads
ensureGradientVisibility();
// Also verify after a short delay to catch any CSS that might override
setTimeout(ensureGradientVisibility, 100);

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
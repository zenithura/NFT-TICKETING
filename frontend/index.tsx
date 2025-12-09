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

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
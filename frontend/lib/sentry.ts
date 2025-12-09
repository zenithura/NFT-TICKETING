/**
 * Sentry error tracking configuration for frontend
 */
import * as Sentry from "@sentry/react";

const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN || "";
const ENVIRONMENT = import.meta.env.MODE || "development";

export function initSentry() {
  if (!SENTRY_DSN) {
    console.warn("Sentry DSN not configured. Error tracking disabled.");
    return;
  }

  Sentry.init({
    dsn: SENTRY_DSN,
    environment: ENVIRONMENT,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    // Performance Monitoring
    tracesSampleRate: ENVIRONMENT === "production" ? 0.1 : 1.0,
    // Session Replay
    replaysSessionSampleRate: ENVIRONMENT === "production" ? 0.1 : 1.0,
    replaysOnErrorSampleRate: 1.0,
    // Release tracking
    release: import.meta.env.VITE_APP_VERSION || "1.0.0",
    // Filter sensitive data
    beforeSend(event, hint) {
      // Don't send events in development unless explicitly enabled
      if (ENVIRONMENT === "development" && !import.meta.env.VITE_SENTRY_ENABLE_DEV) {
        return null;
      }
      return event;
    },
    // Ignore WebGL errors in test environments
    ignoreErrors: [
      "Error creating WebGL context",
      "WebGL context",
      "THREE.WebGLRenderer",
      "ResizeObserver loop limit exceeded",
    ],
  });
}

// Lazy initialize Sentry to avoid blocking initial load
// Only initialize in production or when explicitly enabled
if (typeof window !== "undefined" && (import.meta.env.PROD || import.meta.env.VITE_SENTRY_ENABLE_DEV)) {
  // Defer Sentry initialization to avoid blocking main thread
  // Use requestIdleCallback if available, otherwise setTimeout
  const init = () => {
    if ('requestIdleCallback' in window) {
      (window as any).requestIdleCallback(initSentry, { timeout: 2000 });
    } else {
      setTimeout(initSentry, 2000); // Defer by 2 seconds
    }
  };
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}


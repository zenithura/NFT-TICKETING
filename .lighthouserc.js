module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:5173',
        'http://localhost:5173/#/',
        'http://localhost:5173/#/dashboard',
        'http://localhost:5173/#/create-event',
      ],
      numberOfRuns: 3,
      startServerCommand: 'cd frontend && npm run dev',
      startServerReadyPattern: 'ready in',
      startServerReadyTimeout: 60000,
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.5 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'first-contentful-paint': ['warn', { maxNumericValue: 3000 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 4000 }],
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 500 }],
        'speed-index': ['warn', { maxNumericValue: 4000 }],
        'interactive': ['warn', { maxNumericValue: 5000 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};


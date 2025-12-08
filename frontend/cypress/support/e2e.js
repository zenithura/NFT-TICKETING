// You can add global behaviors here

// Import commands.js using ES2015 syntax:
import './commands'

// Prevent Cypress from failing on uncaught exceptions
Cypress.on('uncaught:exception', (err, runnable) => {
  // Returning false here prevents Cypress from failing the test
  // This is useful for apps that may have non-critical errors
  
  // Ignore WebGL context errors (common in headless browsers)
  if (
    err.message.includes('Error creating WebGL context') ||
    err.message.includes('WebGL context') ||
    err.message.includes('WEBGL') ||
    err.message.includes('webgl') ||
    err.message.includes('RENDER WARNING') ||
    err.message.includes('THREE.WebGLRenderer') ||
    err.message.includes('Context lost')
  ) {
    return false; // Prevent test failure
  }
  
  // Ignore ResizeObserver errors (common in tests)
  if (err.message.includes('ResizeObserver loop limit exceeded')) {
    return false;
  }
  
  // Ignore non-critical promise rejections
  if (err.message.includes('Non-Error promise rejection captured')) {
    return false;
  }
  
  // Ignore Three.js errors in Cypress
  if (err.message.includes('THREE.') && window.Cypress) {
    return false;
  }
  
  // Allow other errors to fail the test
  return true;
});


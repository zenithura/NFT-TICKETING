import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:5173",
    video: false,
    screenshotOnRunFailure: true,
    supportFile: "cypress/support/e2e.js",
    // Auto-detect all test files: supports both .cy.* and .spec.* naming conventions
    // Matches all test files in cypress/e2e/ and subdirectories
    // Automatically includes any new test files added in the future
    specPattern: [
      "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",
      "cypress/e2e/**/*.spec.{js,jsx,ts,tsx}"
    ],
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    // Suppress WebGL-related errors in Cypress
    chromeWebSecurity: false,
    // Environment variables for test detection
    env: {
      CYPRESS: true,
    },
    // Enable test isolation for better reliability
    testIsolation: true,
  },
});


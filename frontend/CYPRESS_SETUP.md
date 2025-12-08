# Cypress E2E Testing Setup Complete ✅

## Overview

Full Cypress E2E testing setup has been added to the frontend folder. The setup includes:

- ✅ Cypress installation and configuration
- ✅ 3 core E2E tests (homepage, event creation, wallet connect)
- ✅ Support files and custom commands
- ✅ Proper folder structure
- ✅ Gitignore configuration

## Installation

To install Cypress dependencies, run:

```bash
cd frontend
npm install
```

This will install Cypress as a dev dependency.

## Running Tests

### Interactive Mode (Recommended for Development)

```bash
npm run e2e
```

This opens the Cypress Test Runner GUI where you can:
- Select which tests to run
- Watch tests execute in real-time
- Debug test failures
- See detailed test output

### Headless Mode (Recommended for CI/CD)

```bash
npm run e2e:headless
```

This runs all tests in headless mode, perfect for:
- Continuous Integration pipelines
- Automated testing
- Quick test execution

## Test Files

### 1. `cypress/e2e/home.cy.js`
Tests the homepage:
- ✅ Page loads without crashing
- ✅ Navigation bar is displayed
- ✅ Marketplace content is visible
- ✅ Page is interactive

### 2. `cypress/e2e/create_event.cy.js`
Tests the event creation flow:
- ✅ Navigation to create event page
- ✅ Form field filling (name, description, date, location, tickets, price)
- ✅ Form validation
- ✅ Handles authentication requirements gracefully

### 3. `cypress/e2e/wallet.cy.js`
Tests wallet connection:
- ✅ Wallet connect button visibility
- ✅ Mocked wallet connection flow
- ✅ Web3 provider mocking
- ✅ Wallet state handling

## Configuration

### `cypress.config.js`
- Base URL: `http://localhost:3000` (matches vite.config.ts port)
- Videos disabled (can be enabled if needed)
- Screenshots on failure enabled
- Viewport: 1280x720
- Command timeout: 10 seconds

### Support Files

- `cypress/support/e2e.js`: Global test configuration and uncaught exception handling
- `cypress/support/commands.js`: Custom Cypress commands (Web3 mocking, wallet helpers)

## Prerequisites

Before running tests:

1. **Start the development server:**
   ```bash
   npm run dev
   ```

2. **Ensure the app is accessible at:**
   ```
   http://localhost:3000
   ```

3. **Backend should be running** (for API-dependent tests)

## Project Structure

```
frontend/
├── cypress/
│   ├── e2e/                 # Test files
│   │   ├── home.cy.js
│   │   ├── create_event.cy.js
│   │   └── wallet.cy.js
│   ├── fixtures/            # Test data
│   │   └── example.json
│   ├── support/             # Support files
│   │   ├── e2e.js
│   │   └── commands.js
│   ├── screenshots/         # (gitignored)
│   ├── videos/              # (gitignored)
│   └── README.md
├── cypress.config.js        # Cypress configuration
└── package.json             # Updated with Cypress scripts
```

## Features

### Error Detection
Cypress will automatically detect:
- JavaScript errors
- Network request failures
- Element not found errors
- Timeout errors
- Assertion failures

### Mocking Support
Tests include:
- Web3 provider mocking
- Wallet connection mocking
- API response handling

### Robust Selectors
Tests use multiple selector strategies:
- Element names
- Data attributes (where available)
- Text content
- ARIA labels
- Multiple fallback selectors

## Next Steps

1. **Run tests to verify setup:**
   ```bash
   npm run e2e:headless
   ```

2. **Add more tests** as features are developed:
   - Ticket purchasing flow
   - Marketplace browsing
   - User dashboard
   - Event details page
   - Resale functionality

3. **Add data-testid attributes** to components for more reliable selectors:
   ```jsx
   <button data-testid="connect-wallet-button">Connect Wallet</button>
   ```

4. **Configure CI/CD** to run tests automatically:
   ```yaml
   # Example GitHub Actions
   - run: npm run e2e:headless
   ```

## Troubleshooting

### Tests failing with "connection refused"
- Ensure dev server is running on port 3000
- Check if port is available: `lsof -i :3000`

### Tests timing out
- Increase `defaultCommandTimeout` in `cypress.config.js`
- Check network requests are completing

### Wallet connection not working in tests
- Verify Web3 provider is properly mocked
- Check browser console for errors
- Ensure ethereum object is injected before tests run

### HashRouter routing issues
- Tests are configured for HashRouter (`/#/route`)
- Verify routes use hash-based navigation

## Resources

- [Cypress Documentation](https://docs.cypress.io/)
- [Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Custom Commands](https://docs.cypress.io/api/cypress-api/custom-commands)

---

**Setup completed on:** 2025-01-28  
**Cypress version:** ^13.6.0


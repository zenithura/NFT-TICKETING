# Cypress E2E Testing

This directory contains end-to-end tests for the NFT Ticketing Platform.

## Structure

```
cypress/
├── e2e/              # Test files
│   ├── home.cy.js           # Homepage tests
│   ├── create_event.cy.js   # Event creation flow tests
│   └── wallet.cy.js         # Wallet connection tests
├── fixtures/         # Test data
├── support/          # Support files and custom commands
│   ├── e2e.js       # Global test configuration
│   └── commands.js  # Custom Cypress commands
└── screenshots/      # Screenshots (gitignored)
└── videos/          # Videos (gitignored)
```

## Running Tests

### Interactive Mode (GUI)
```bash
npm run e2e
```

### Headless Mode (CI/CD)
```bash
npm run e2e:headless
```

## Test Files

### home.cy.js
Tests for the homepage:
- Page loads without crashing
- Navigation bar is displayed
- Marketplace content is visible

### create_event.cy.js
Tests for event creation:
- Form navigation
- Form field filling
- Form validation

### wallet.cy.js
Tests for wallet connection:
- Wallet connect button visibility
- Mocked wallet connection flow
- Wallet state handling

## Prerequisites

Before running tests:
1. Start the development server: `npm run dev`
2. Ensure the app is running on `http://localhost:3000`

## Writing New Tests

1. Create a new test file in `cypress/e2e/`
2. Use descriptive test names
3. Follow the existing test patterns
4. Use data-testid attributes when possible for better selectors

## Notes

- Tests are configured to handle HashRouter routing
- Web3 provider is mocked in tests
- Tests handle authentication states gracefully


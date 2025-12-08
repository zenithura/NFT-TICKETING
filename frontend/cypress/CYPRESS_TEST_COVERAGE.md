# Cypress E2E Test Coverage

## Overview

This directory contains comprehensive end-to-end (E2E) tests for all frontend pages and components. Tests are automatically discovered and run by Cypress.

## Test Files

All test files follow the naming convention: `*.cy.js`

### Page Tests

1. **home.cy.js** - Homepage/Marketplace smoke tests
2. **login.cy.js** - User login page tests
3. **register.cy.js** - User registration page tests
4. **forgot_password.cy.js** - Password recovery page tests
5. **reset_password.cy.js** - Password reset page tests
6. **dashboard.cy.js** - User dashboard tests (requires authentication)
7. **create_event.cy.js** - Event creation page tests (requires organizer role)
8. **event_details.cy.js** - Event details page tests
9. **scanner.cy.js** - Ticket scanner page tests (requires authentication)
10. **admin_login.cy.js** - Admin login page tests
11. **admin_dashboard.cy.js** - Admin dashboard tests (requires admin authentication)
12. **marketplace.cy.js** - Marketplace page comprehensive tests
13. **wallet.cy.js** - Wallet connection tests

## Automatic Test Discovery

Cypress automatically discovers all test files matching:
- `cypress/e2e/**/*.cy.{js,jsx,ts,tsx}`
- `cypress/e2e/**/*.spec.{js,jsx,ts,tsx}`

**Adding a new test file:**
1. Create a new file in `cypress/e2e/` with the pattern `*.cy.js`
2. Cypress will automatically detect and run it
3. No configuration changes needed

## Running Tests

### Interactive Mode (Cypress UI)
```bash
npm run e2e
```

### Headless Mode (CI/CD)
```bash
npm run e2e:headless
```

### Run Specific Test File
```bash
npx cypress run --spec "cypress/e2e/login.cy.js"
```

## Test Structure

Each test file follows this pattern:

```javascript
describe("Page Name", () => {
  beforeEach(() => {
    // Setup: visit page, mock providers, etc.
    cy.visitPage("/#/route");
  });

  it("loads without crashing", () => {
    // Verify page loads
    cy.checkPageLoad(['expected-selectors']);
  });

  it("displays key elements", () => {
    // Verify DOM elements exist
  });

  it("handles user interaction", () => {
    // Test user interactions
  });
});
```

## Custom Commands

Available in `cypress/support/commands.js`:

- `cy.visitPage(path)` - Visit page with built-in wait
- `cy.checkPageLoad(elements)` - Verify page loaded correctly
- `cy.waitForAPI()` - Wait for API calls to complete
- `cy.mockWeb3Provider()` - Mock Web3/ethereum provider
- `cy.login(email, password)` - Mock user login
- `cy.loginAsAdmin()` - Mock admin login

## WebGL Error Handling

All WebGL-related errors are automatically suppressed in Cypress tests via `cypress/support/e2e.js`. Tests will not fail due to WebGL context errors in headless browsers.

## Protected Routes

Some pages require authentication:
- **Dashboard** - Requires user authentication
- **Create Event** - Requires organizer role
- **Scanner** - Requires user authentication
- **Admin Dashboard** - Requires admin authentication

For protected routes, tests check that:
1. Page loads (may redirect to login)
2. Expected behavior based on auth state
3. Error handling works correctly

## Best Practices

1. **Use data-cy attributes** - Prefer `data-cy` over CSS classes for selectors
2. **Wait for API calls** - Use `cy.waitForAPI()` after visiting pages that fetch data
3. **Mock Web3 provider** - Use `cy.mockWeb3Provider()` for pages using Web3
4. **Test error states** - Verify pages handle errors gracefully
5. **Keep tests fast** - Use minimal waits, focus on critical paths

## Adding Tests for New Pages

When adding a new page:

1. **Create test file**: `cypress/e2e/new_page.cy.js`

```javascript
describe("New Page", () => {
  beforeEach(() => {
    cy.visitPage("/#/new-page");
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['main']);
  });

  it("displays expected content", () => {
    cy.get('[data-cy="page-title"]').should("exist");
  });
});
```

2. **Add data-cy attributes** to your React component:
```tsx
<h1 data-cy="page-title">Page Title</h1>
```

3. **Run tests** - Cypress will automatically detect and run your new test

## Future Enhancements

- Component-level tests for reusable components
- Visual regression testing
- Performance testing
- Accessibility testing integration


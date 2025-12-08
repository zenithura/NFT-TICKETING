// Custom Cypress commands can be added here

// Example: Custom command to wait for wallet connection
Cypress.Commands.add('waitForWalletConnection', () => {
  cy.wait(1000); // Wait for wallet to connect
});

// Example: Custom command to mock Web3 provider
Cypress.Commands.add('mockWeb3Provider', () => {
  cy.window().then((win) => {
    win.ethereum = {
      request: cy.stub().resolves(["0x1234567890abcdef1234567890abcdef12345678"]),
      isMetaMask: true,
      selectedAddress: "0x1234567890abcdef1234567890abcdef12345678",
    };
  });
});

// Command: Mock authenticated user session
Cypress.Commands.add('login', (email = 'test@example.com', password = 'Test123!@#') => {
  cy.session([email, password], () => {
    cy.visit('/#/login');
    cy.wait(1000);
    cy.get('input[type="email"]').type(email);
    cy.get('input[type="password"]').type(password);
    cy.get('form').submit();
    cy.wait(2000); // Wait for login to complete
  });
});

// Command: Mock admin authenticated session
Cypress.Commands.add('loginAsAdmin', () => {
  cy.session('admin', () => {
    cy.visit('/#/admin/login');
    cy.wait(1000);
    // Admin login logic - adjust based on your admin auth
    cy.get('input[type="email"]').type('admin@example.com');
    cy.get('input[type="password"]').type('Admin123!@#');
    cy.get('form').submit();
    cy.wait(2000);
  });
});

// Command: Visit page and wait for it to be ready
Cypress.Commands.add('visitPage', (path, options = {}) => {
  cy.visit(path, options);
  cy.wait(1000); // Wait for page load
  cy.get('body').should('be.visible'); // Ensure page is visible
});

// Command: Check if page loaded without errors
Cypress.Commands.add('checkPageLoad', (expectedElements = []) => {
  // Check no error boundaries are showing
  cy.get('body').should('not.contain', 'Something went wrong');
  cy.get('body').should('not.contain', 'Error');
  
  // Check expected elements exist
  expectedElements.forEach((selector) => {
    cy.get(selector).should('exist');
  });
});

// Command: Wait for API calls to complete
Cypress.Commands.add('waitForAPI', () => {
  cy.wait(2000); // Wait for API calls
});

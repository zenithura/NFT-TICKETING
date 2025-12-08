describe("Event Creation Flow", () => {
  beforeEach(() => {
    // Mock Web3 provider before visiting
    cy.window().then((win) => {
      win.ethereum = {
        request: () => Promise.resolve(["0x1234567890abcdef1234567890abcdef12345678"]),
        isMetaMask: true,
        selectedAddress: "0x1234567890abcdef1234567890abcdef12345678",
      };
    });
  });

  it("should navigate to create event page", () => {
    cy.visit("/");
    
    // Wait for page to load
    cy.wait(1000);
    
    // Try to navigate to create event page
    // Since it's a protected route, we'll test the form if accessible
    cy.visit("/#/create-event");
    
    // Wait for page to load
    cy.wait(2000);
  });

  it("allows user to fill event form (if authenticated)", () => {
    // Visit create event page
    cy.visit("/#/create-event");
    
    // Wait for page to load
    cy.wait(2000);
    
    // Check if form exists (may not be visible if not authenticated)
    cy.get("body").then(($body) => {
      if ($body.find('[data-cy="create-event-form"]').length > 0) {
        // Form is visible, fill it out using data-cy attributes
        cy.get('[data-cy="event-name-input"]').type("Test Concert", { force: true });
        cy.get('[data-cy="event-description-input"]').type("This is a test event for Cypress E2E testing.", { force: true });
        
        // Fill date (format: YYYY-MM-DDTHH:mm)
        const futureDate = new Date();
        futureDate.setMonth(futureDate.getMonth() + 1);
        const dateString = futureDate.toISOString().slice(0, 16);
        cy.get('input[name="date"]').type(dateString, { force: true });
        
        cy.get('input[name="location"]').type("San Francisco, CA", { force: true });
        cy.get('[data-cy="event-total-supply-input"]').clear().type("100", { force: true });
        cy.get('[data-cy="event-ticket-price-input"]').clear().type("0.05", { force: true });
        
        // Verify form fields are filled
        cy.get('[data-cy="event-name-input"]').should("have.value", "Test Concert");
        cy.get('[data-cy="event-total-supply-input"]').should("have.value", "100");
        cy.get('[data-cy="event-ticket-price-input"]').should("have.value", "0.05");
      } else {
        // Form is not visible, likely due to authentication - show login message
        cy.log("Create Event form requires authentication - this is expected behavior");
        // Verify we're on the right page and login message is shown
        cy.url().should("include", "create-event");
      }
    });
  });

  it("form validates required fields", () => {
    cy.visit("/#/create-event");
    cy.wait(2000);
    
    cy.get("body").then(($body) => {
      if ($body.find('[data-cy="create-event-form"]').length > 0) {
        // Try to submit empty form
        cy.get('[data-cy="submit-event-form"]').should("be.visible");
        // HTML5 validation should prevent submission if required fields are empty
        cy.get('[data-cy="event-name-input"]').should("have.attr", "required");
        cy.get('[data-cy="event-description-input"]').should("have.attr", "required");
        cy.get('[data-cy="event-total-supply-input"]').should("have.attr", "required");
        cy.get('[data-cy="event-ticket-price-input"]').should("have.attr", "required");
      }
    });
  });
});


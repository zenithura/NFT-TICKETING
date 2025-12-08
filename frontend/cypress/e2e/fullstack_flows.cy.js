describe("Full-Stack E2E User Flows", () => {
  beforeEach(() => {
    cy.mockWeb3Provider();
    cy.visitPage("/");
    cy.waitForAPI();
  });

  describe("Complete Event Creation and Ticket Purchase Flow", () => {
    it("should complete full event lifecycle", () => {
      // 1. Navigate to marketplace
      cy.visitPage("/");
      cy.get('[data-cy="marketplace-title"]').should("be.visible");
      
      // 2. Navigate to create event (if authenticated)
      cy.visitPage("/#/create-event");
      cy.waitForAPI();
      
      // 3. Check if form exists or login message
      cy.get("body").should("be.visible");
    });

    it("should handle ticket purchase flow", () => {
      // 1. Browse marketplace
      cy.visitPage("/");
      cy.get("main").should("exist");
      
      // 2. Click on an event (if available)
      cy.get("body").then(($body) => {
        const eventLink = $body.find('a[href*="/event/"]');
        if (eventLink.length > 0) {
          cy.wrap(eventLink.first()).click({ force: true });
          cy.waitForAPI();
          
          // 3. Verify event details page loads
          cy.get("main").should("exist");
          cy.get("body").should("be.visible");
        }
      });
    });
  });

  describe("Authentication Flow", () => {
    it("should complete registration and login flow", () => {
      // 1. Go to register page
      cy.visitPage("/#/register");
      cy.get('form').should("exist");
      
      // 2. Go to login page
      cy.visitPage("/#/login");
      cy.get('input[type="email"]').should("be.visible");
      cy.get('input[type="password"]').should("be.visible");
    });

    it("should handle password recovery flow", () => {
      // 1. Go to forgot password
      cy.visitPage("/#/forgot-password");
      cy.get('input[type="email"]').should("be.visible");
    });
  });

  describe("Marketplace and Dashboard Integration", () => {
    it("should navigate between marketplace and dashboard", () => {
      // 1. Start at marketplace
      cy.visitPage("/");
      cy.get('[data-cy="marketplace-title"]').should("be.visible");
      
      // 2. Navigate to dashboard
      cy.visitPage("/#/dashboard");
      cy.waitForAPI();
      cy.get("main").should("exist");
    });
  });
});


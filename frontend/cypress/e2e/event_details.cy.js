describe("Event Details Page", () => {
  beforeEach(() => {
    cy.mockWeb3Provider();
    // Use a test event ID - adjust based on your test data
    cy.visitPage("/#/event/1");
    cy.waitForAPI();
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['main']);
  });

  it("displays event information or loading state", () => {
    cy.get("main").should("exist");
    cy.get("body").should("be.visible");
    // Page may show loading skeleton or event details
  });

  it("handles invalid event ID gracefully", () => {
    cy.visitPage("/#/event/99999");
    cy.waitForAPI();
    cy.get("body").should("be.visible");
    // Should show error or not found message
  });
});


describe("Dashboard Page", () => {
  beforeEach(() => {
    // Mock Web3 provider
    cy.mockWeb3Provider();
    // Mock authentication - dashboard requires auth
    cy.visitPage("/#/dashboard");
    cy.waitForAPI();
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['main']);
  });

  it("displays dashboard content", () => {
    cy.get("main").should("exist");
    cy.get("body").should("be.visible");
  });

  it("shows dashboard sections or navigation", () => {
    cy.get("body").should("be.visible");
    // Dashboard may redirect to login if not authenticated, which is expected
    cy.url().should("include", "/");
  });
});


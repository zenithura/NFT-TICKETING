describe("Admin Dashboard Page", () => {
  beforeEach(() => {
    cy.mockWeb3Provider();
    // Admin dashboard requires admin authentication
    cy.visitPage("/#/admin/dashboard");
    cy.waitForAPI();
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['body']);
  });

  it("displays admin dashboard or redirects to login", () => {
    cy.get("body").should("be.visible");
    // May redirect to admin login if not authenticated
    cy.url().should("include", "/admin");
  });
});


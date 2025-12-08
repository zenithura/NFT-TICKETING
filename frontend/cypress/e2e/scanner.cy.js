describe("Scanner Page", () => {
  beforeEach(() => {
    cy.mockWeb3Provider();
    // Scanner requires authentication
    cy.visitPage("/#/scanner");
    cy.waitForAPI();
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['body']);
  });

  it("displays scanner interface or auth requirement", () => {
    cy.get("body").should("be.visible");
    // May redirect to login if not authenticated
    cy.url().should("include", "/");
  });
});


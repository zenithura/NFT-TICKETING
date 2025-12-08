describe("Marketplace Page", () => {
  beforeEach(() => {
    cy.mockWeb3Provider();
    cy.visitPage("/");
    cy.waitForAPI();
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['main', '[data-cy="marketplace-title"]']);
  });

  it("displays marketplace title", () => {
    cy.get('[data-cy="marketplace-title"]').should("be.visible").and("not.be.empty");
  });

  it("displays marketplace subtitle", () => {
    cy.get('[data-cy="marketplace-subtitle"]').should("be.visible");
  });

  it("shows marketplace content sections", () => {
    cy.get("main").should("exist");
    cy.get("body").should("be.visible");
  });

  it("has search functionality", () => {
    cy.get('input[type="text"]').should("exist");
  });
});


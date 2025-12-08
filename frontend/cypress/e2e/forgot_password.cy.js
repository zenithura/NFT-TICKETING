describe("Forgot Password Page", () => {
  beforeEach(() => {
    cy.visitPage("/#/forgot-password");
  });

  it("loads without crashing", () => {
    cy.checkPageLoad();
  });

  it("displays password reset form", () => {
    cy.get("body").should("be.visible");
    cy.get("form, input[type='email'], button").should("exist");
  });

  it("has email input field", () => {
    cy.get('input[type="email"]').should("be.visible");
  });
});


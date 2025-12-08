describe("Reset Password Page", () => {
  beforeEach(() => {
    cy.visitPage("/#/reset-password");
  });

  it("loads without crashing", () => {
    cy.checkPageLoad();
  });

  it("displays password reset form", () => {
    cy.get("body").should("be.visible");
    cy.get("form, input[type='password'], button").should("exist");
  });

  it("has password input fields", () => {
    cy.get('input[type="password"]').should("exist");
  });
});


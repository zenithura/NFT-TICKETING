describe("Admin Login Page", () => {
  beforeEach(() => {
    cy.visitPage("/#/admin/login");
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['form', 'input']);
  });

  it("displays admin login form", () => {
    cy.get("form").should("exist");
    cy.get('input[type="email"], input[type="text"]').should("exist");
    cy.get('input[type="password"]').should("exist");
  });

  it("has form inputs", () => {
    cy.get('input').should("have.length.greaterThan", 0);
    cy.get('button[type="submit"], button').should("exist");
  });
});


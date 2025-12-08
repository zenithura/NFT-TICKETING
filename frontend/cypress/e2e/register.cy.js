describe("Register Page", () => {
  beforeEach(() => {
    cy.visitPage("/#/register");
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['form']);
  });

  it("displays registration form", () => {
    cy.get('form').should("exist");
    cy.get('input[type="email"]').should("be.visible");
    cy.get('input[type="password"]').should("exist");
  });

  it("has form validation", () => {
    cy.get('input[type="email"]').should("have.attr", "required");
    cy.get('input[type="password"]').should("have.attr", "required");
  });

  it("allows form interaction", () => {
    cy.get('input[type="email"]').type("newuser@example.com");
    cy.get('input[type="email"]').should("have.value", "newuser@example.com");
  });
});


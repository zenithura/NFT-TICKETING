describe("Login Page", () => {
  beforeEach(() => {
    cy.visitPage("/#/login");
  });

  it("loads without crashing", () => {
    cy.checkPageLoad(['form', 'input[type="email"]', 'input[type="password"]']);
  });

  it("displays login form elements", () => {
    cy.get('input[type="email"]').should("be.visible");
    cy.get('input[type="password"]').should("be.visible");
    cy.get('form').should("exist");
  });

  it("has working form inputs", () => {
    cy.get('input[type="email"]').type("test@example.com");
    cy.get('input[type="password"]').type("password123");
    cy.get('input[type="email"]').should("have.value", "test@example.com");
  });

  it("shows navigation or links", () => {
    cy.get("body").should("be.visible");
    // Check for register link or navigation
    cy.get("a").should("exist");
  });
});


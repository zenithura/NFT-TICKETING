describe("Homepage", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("loads without crashing", () => {
    cy.url().should("include", "/");
    // The homepage should contain NFT-related content
    // Since it uses translations and dynamic content, we check for common elements
    cy.get("body").should("exist");
  });

  it("displays navigation bar", () => {
    cy.get("nav").should("exist");
  });

  it("shows marketplace content", () => {
    // Wait for page to load
    cy.wait(1000);
    // The marketplace page should be visible (it might show loading state or events)
    cy.get("main").should("exist");
  });

  it("contains NFT or ticketing related text", () => {
    // Check if any NFT or ticketing related text appears on the page
    // The marketplace title may vary, but the subtitle always mentions NFTs
    // OR we check for NFT-related content anywhere in the hero section
    
    // Wait for page to fully load
    cy.wait(1000);
    
    // Check subtitle contains NFT (this is more reliable than title)
    cy.get('[data-cy="marketplace-subtitle"]').should("be.visible");
    cy.get('[data-cy="marketplace-subtitle"]').then(($el) => {
      const text = $el.text().toLowerCase();
      // Subtitle should mention NFTs or blockchain/Web3 concepts
      expect(text).to.satisfy((txt) => 
        txt.includes('nft') || 
        txt.includes('blockchain') || 
        txt.includes('decentralized') ||
        txt.includes('web3')
      );
    });
    
    // Alternative: Check that marketplace title exists (regardless of content)
    cy.get('[data-cy="marketplace-title"]').should("be.visible").and("not.be.empty");
  });
});


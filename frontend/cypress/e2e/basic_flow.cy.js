describe('NFT Ticketing Platform - Basic Flow', () => {
    beforeEach(() => {
        // Visit the app root
        cy.visit('http://localhost:5173')
    })

    it('loads the homepage successfully', () => {
        // Check for main logo text "NFTix"
        cy.contains('NFTix').should('be.visible')
        // Check if navigation exists
        cy.get('nav').should('exist')
    })

    it('can navigate to browse section', () => {
        // The "Browse" link points to #browse-events
        cy.contains('Browse').click()
        // Check if the section exists in the DOM (it might be lazy loaded or just scrolled to)
        cy.get('#browse-events').should('exist')
    })

    it('shows connect wallet button', () => {
        // Look for button that contains "Connect" (case insensitive)
        cy.contains(/connect/i).should('be.visible')
    })
})

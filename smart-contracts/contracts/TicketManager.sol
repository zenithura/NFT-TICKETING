// File header: ERC721-based smart contract for NFT ticketing system.
// Enforces ticket ownership, resale marketplace, and scanning functionality on-chain.
// The FastAPI backend handles business logic while this contract provides blockchain guarantees.

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title TicketManager
 * @dev ERC721-based ticketing contract tailored for the NFT Ticketing project.
 * FastAPI backend is expected to hold the authoritative business logic while this
 * contract enforces ownership, resale caps, and scanning/invalidations on-chain.
 */
contract TicketManager is ERC721URIStorage, AccessControl, ReentrancyGuard {
    // Purpose: Access control roles for minting and scanning operations.
    // Side effects: None - constants only.
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant SCANNER_ROLE = keccak256("SCANNER_ROLE");

    // Purpose: Stores event association and scan status for each ticket.
    // Side effects: None - struct definition only.
    struct TicketInfo {
        uint256 eventId;
        bool scanned;
    }

    // Purpose: Stores seller address and price for tickets listed on marketplace.
    // Side effects: None - struct definition only.
    struct ResaleListing {
        address seller;
        uint256 price;
    }

    // Purpose: Maps token ID to ticket metadata (event ID and scan status).
    // Side effects: None - storage mapping.
    mapping(uint256 => TicketInfo) private _ticketInfo;

    // Purpose: Maps token ID to resale listing information.
    // Side effects: None - storage mapping.
    mapping(uint256 => ResaleListing) private _listings;

    // Purpose: Counter for generating unique token IDs, starts at 1.
    // Side effects: None - public state variable.
    uint256 public nextTokenId = 1;

    // Purpose: Royalty recipient address and basis points (1% = 100 bps) for resale fees.
    // Side effects: None - public state variables.
    address public royaltyRecipient;
    uint96 public royaltyBps;

    // Purpose: Event emitted when a new ticket NFT is minted.
    // Side effects: None - event definition only.
    event TicketMinted(uint256 indexed tokenId, address indexed to, uint256 indexed eventId);
    // Purpose: Event emitted when a ticket is listed for resale.
    event TicketListed(uint256 indexed tokenId, address indexed seller, uint256 price);
    // Purpose: Event emitted when a resale listing is cancelled.
    event TicketListingCancelled(uint256 indexed tokenId);
    // Purpose: Event emitted when a listed ticket is purchased.
    event TicketSold(uint256 indexed tokenId, address indexed buyer, uint256 price);
    // Purpose: Event emitted when a ticket is scanned at event entry.
    event TicketScanned(uint256 indexed tokenId, address indexed scanner);

    // Purpose: Initialize contract with admin, royalty settings, and access roles.
    // Params: admin — contract administrator address; defaultRoyaltyRecipient — royalty receiver; defaultRoyaltyBps — royalty percentage in basis points.
    // Side effects: Sets royalty parameters, grants admin/minter/scanner roles to admin.
    constructor(
        address admin,
        address defaultRoyaltyRecipient,
        uint96 defaultRoyaltyBps
    ) ERC721("NFT Ticket", "N-TIX") {
        require(admin != address(0), "Admin required");
        require(defaultRoyaltyRecipient != address(0), "Royalty recipient required");
        royaltyRecipient = defaultRoyaltyRecipient;
        royaltyBps = defaultRoyaltyBps;

        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(SCANNER_ROLE, admin);
    }

    /**
     * @notice Set royalty parameters used on every resale.
     * Purpose: Update royalty recipient and percentage for resale transactions.
     * Params: recipient — address to receive royalties; bps — basis points (max 2000 = 20%).
     * Side effects: Updates contract state, restricted to admin role.
     */
    function setRoyalty(address recipient, uint96 bps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(recipient != address(0), "recipient req");
        require(bps <= 2_000, "royalty too high"); // max 20%
        royaltyRecipient = recipient;
        royaltyBps = bps;
    }

    /**
     * @notice Mint a new ticket NFT and persist its metadata.
     * Purpose: Create a new ERC721 token representing a ticket for an event.
     * Params: to — recipient wallet address; eventId — event identifier; tokenUri — metadata URI.
     * Returns: tokenId — newly minted token identifier.
     * Side effects: Mints NFT, sets URI, stores ticket info, emits TicketMinted event, restricted to minter role.
     */
    function mintTicket(
        address to,
        uint256 eventId,
        string memory tokenUri
    ) external onlyRole(MINTER_ROLE) returns (uint256 tokenId) {
        require(to != address(0), "invalid recipient");
        require(eventId != 0, "event required");

        tokenId = nextTokenId++;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenUri);
        _ticketInfo[tokenId] = TicketInfo({eventId: eventId, scanned: false});

        emit TicketMinted(tokenId, to, eventId);
    }

    /**
     * @notice List an owned ticket for resale.
     * Purpose: Create a marketplace listing for a ticket owned by the caller.
     * Params: tokenId — ticket to list; price — listing price in wei.
     * Side effects: Updates listings mapping, emits TicketListed event, verifies ownership.
     */
    function listTicket(uint256 tokenId, uint256 price) external {
        _checkAuthorized(_ownerOf(tokenId), msg.sender, tokenId);
        require(price > 0, "price required");
        _listings[tokenId] = ResaleListing({seller: msg.sender, price: price});
        emit TicketListed(tokenId, msg.sender, price);
    }

    /**
     * @notice Cancel an existing listing.
     * Purpose: Remove a ticket from the marketplace, allowing only seller or admin.
     * Params: tokenId — ticket listing to cancel.
     * Side effects: Deletes listing from mapping, emits TicketListingCancelled event.
     */
    function cancelListing(uint256 tokenId) external {
        ResaleListing memory listing = _listings[tokenId];
        require(listing.seller != address(0), "not listed");
        require(listing.seller == msg.sender || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "not seller");
        delete _listings[tokenId];
        emit TicketListingCancelled(tokenId);
    }

    /**
     * @notice Purchase a listed ticket. Royalties are split automatically.
     * Purpose: Purchase a listed ticket, transferring ETH to seller and royalty recipient, then transferring NFT.
     * Params: tokenId — ticket to purchase (msg.value must cover listing price).
     * Side effects: Deletes listing, transfers ETH, transfers NFT ownership, emits TicketSold event, protected by reentrancy guard.
     */
    function buyTicket(uint256 tokenId) external payable nonReentrant {
        ResaleListing memory listing = _listings[tokenId];
        require(listing.seller != address(0), "not listed");
        require(msg.value >= listing.price, "insufficient funds");

        delete _listings[tokenId];

        // Purpose: Calculate royalty amount and seller payout from listing price.
        uint256 royalty = (listing.price * royaltyBps) / 10_000;
        uint256 payout = listing.price - royalty;

        // Purpose: Transfer royalty fee to recipient address.
        if (royalty > 0) {
            (bool royaltyOk, ) = royaltyRecipient.call{value: royalty}("");
            require(royaltyOk, "royalty transfer failed");
        }

        // Purpose: Transfer remaining payment to seller.
        (bool sellerOk, ) = listing.seller.call{value: payout}("");
        require(sellerOk, "seller transfer failed");

        _transfer(listing.seller, msg.sender, tokenId);
        emit TicketSold(tokenId, msg.sender, listing.price);
    }

    /**
     * @notice Mark a ticket as scanned to prevent re-entry.
     * Purpose: Mark a ticket as used/scanned to prevent reuse at event entry.
     * Params: tokenId — ticket to scan.
     * Side effects: Updates ticket scan status, emits TicketScanned event, restricted to scanner role.
     */
    function scanTicket(uint256 tokenId) external onlyRole(SCANNER_ROLE) {
        _requireOwned(tokenId);
        TicketInfo storage info = _ticketInfo[tokenId];
        require(!info.scanned, "already scanned");
        info.scanned = true;
        emit TicketScanned(tokenId, msg.sender);
    }

    /**
     * @notice Burns a ticket. Only admins can invalidate a ticket once used/refunded.
     * Purpose: Permanently destroy a ticket NFT, typically after refund or invalidation.
     * Params: tokenId — ticket to burn.
     * Side effects: Burns NFT, deletes ticket info and listing, restricted to admin role.
     */
    function burnTicket(uint256 tokenId) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _requireOwned(tokenId);
        _burn(tokenId);
        delete _ticketInfo[tokenId];
        delete _listings[tokenId];
    }

    /**
     * @notice Returns the metadata for a ticket.
     * Purpose: Retrieve ticket information and listing status for a given token.
     * Params: tokenId — ticket identifier.
     * Returns: info — ticket metadata (event ID, scan status); listing — resale listing details if listed.
     * Side effects: Read-only view function, verifies token exists.
     */
    function getTicketInfo(uint256 tokenId) external view returns (TicketInfo memory info, ResaleListing memory listing) {
        _requireOwned(tokenId);
        return (_ticketInfo[tokenId], _listings[tokenId]);
    }

    /**
     * @dev Required override for Solidity multiple inheritance.
     * Purpose: Implement ERC165 interface support for multiple inheritance compatibility.
     * Params: interfaceId — interface identifier to check.
     * Returns: bool — whether contract supports the interface.
     * Side effects: Read-only view function.
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721URIStorage, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}


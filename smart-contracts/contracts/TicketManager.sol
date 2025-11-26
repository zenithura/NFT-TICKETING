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
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant SCANNER_ROLE = keccak256("SCANNER_ROLE");

    struct TicketInfo {
        uint256 eventId;
        bool scanned;
    }

    struct ResaleListing {
        address seller;
        uint256 price;
    }

    // tokenId => ticket metadata
    mapping(uint256 => TicketInfo) private _ticketInfo;

    // tokenId => listing details
    mapping(uint256 => ResaleListing) private _listings;

    // monotonically increasing token id counter
    uint256 public nextTokenId = 1;

    // royalty recipient + basis points (1% = 100 bps)
    address public royaltyRecipient;
    uint96 public royaltyBps;

    event TicketMinted(uint256 indexed tokenId, address indexed to, uint256 indexed eventId);
    event TicketListed(uint256 indexed tokenId, address indexed seller, uint256 price);
    event TicketListingCancelled(uint256 indexed tokenId);
    event TicketSold(uint256 indexed tokenId, address indexed buyer, uint256 price);
    event TicketScanned(uint256 indexed tokenId, address indexed scanner);

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
     */
    function setRoyalty(address recipient, uint96 bps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(recipient != address(0), "recipient req");
        require(bps <= 2_000, "royalty too high"); // max 20%
        royaltyRecipient = recipient;
        royaltyBps = bps;
    }

    /**
     * @notice Mint a new ticket NFT and persist its metadata.
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
     */
    function listTicket(uint256 tokenId, uint256 price) external {
        _checkAuthorized(_ownerOf(tokenId), msg.sender, tokenId);
        require(price > 0, "price required");
        _listings[tokenId] = ResaleListing({seller: msg.sender, price: price});
        emit TicketListed(tokenId, msg.sender, price);
    }

    /**
     * @notice Cancel an existing listing.
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
     */
    function buyTicket(uint256 tokenId) external payable nonReentrant {
        ResaleListing memory listing = _listings[tokenId];
        require(listing.seller != address(0), "not listed");
        require(msg.value >= listing.price, "insufficient funds");

        delete _listings[tokenId];

        uint256 royalty = (listing.price * royaltyBps) / 10_000;
        uint256 payout = listing.price - royalty;

        if (royalty > 0) {
            (bool royaltyOk, ) = royaltyRecipient.call{value: royalty}("");
            require(royaltyOk, "royalty transfer failed");
        }

        (bool sellerOk, ) = listing.seller.call{value: payout}("");
        require(sellerOk, "seller transfer failed");

        _transfer(listing.seller, msg.sender, tokenId);
        emit TicketSold(tokenId, msg.sender, listing.price);
    }

    /**
     * @notice Mark a ticket as scanned to prevent re-entry.
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
     */
    function burnTicket(uint256 tokenId) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _requireOwned(tokenId);
        _burn(tokenId);
        delete _ticketInfo[tokenId];
        delete _listings[tokenId];
    }

    /**
     * @notice Returns the metadata for a ticket.
     */
    function getTicketInfo(uint256 tokenId) external view returns (TicketInfo memory info, ResaleListing memory listing) {
        _requireOwned(tokenId);
        return (_ticketInfo[tokenId], _listings[tokenId]);
    }

    /**
     * @dev Required override for Solidity multiple inheritance.
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


// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract NFTTicket is ERC721URIStorage, AccessControl, ReentrancyGuard, ERC2981, Pausable {
    uint256 private _nextTokenId;

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");

    // Price validation constants
    uint256 public constant MAX_RESALE_MULTIPLIER = 5; // 5x original price max
    uint256 public constant MIN_RESALE_PRICE = 0.001 ether; // Minimum 0.001 ETH
    uint256 public constant RESALE_COOLDOWN = 1 hours; // 1 hour cooldown between resales
    
    // Rate limiting constants
    uint256 public constant MAX_MINTS_PER_ADDRESS = 100; // Max tickets per address
    uint256 public constant MAX_BUYS_PER_BLOCK = 10; // Max purchases per block per address
    uint256 public constant RATE_LIMIT_WINDOW = 1 hours; // Rate limit window

    struct TicketData {
        uint256 eventId;
        uint256 price;
        bool forSale;
        uint256 eventDate; // Unix timestamp when event occurs
        uint256 lastResaleTime; // Timestamp of last resale
        bool used; // Whether ticket has been used/validated
    }

    mapping(uint256 => TicketData) public tickets;
    
    // Rate limiting mappings
    mapping(address => uint256) public mintCount; // Total mints per address
    mapping(address => uint256) public buyCount; // Buys in current window
    mapping(address => uint256) public lastBuyWindow; // Last buy window timestamp

    event TicketMinted(uint256 indexed tokenId, address indexed owner, uint256 eventId, uint256 price, uint256 eventDate);
    event TicketListed(uint256 indexed tokenId, uint256 price);
    event TicketSold(uint256 indexed tokenId, address indexed from, address indexed to, uint256 price);
    event TicketValidated(uint256 indexed tokenId, address indexed validator);
    event ContractPaused(address indexed account);
    event ContractUnpaused(address indexed account);

    constructor() ERC721("NFTTicket", "NFTIX") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        
        // Set default royalty to 5% (500 basis points)
        _setDefaultRoyalty(msg.sender, 500);
    }

    /**
     * @notice Mint a new ticket
     * @param to Address to mint the ticket to
     * @param uri Token URI for metadata
     * @param eventId ID of the event
     * @param price Initial price of the ticket
     * @param eventDate Unix timestamp when the event occurs
     */
    function mintTicket(
        address to,
        string memory uri,
        uint256 eventId,
        uint256 price,
        uint256 eventDate
    ) public onlyRole(MINTER_ROLE) whenNotPaused {
        require(to != address(0), "Cannot mint to zero address");
        require(price >= MIN_RESALE_PRICE, "Price below minimum");
        require(eventDate > block.timestamp, "Event date must be in future");
        
        // Rate limiting: Check mint count per address
        require(mintCount[to] < MAX_MINTS_PER_ADDRESS, "Max mints exceeded for address");
        mintCount[to]++;

        uint256 tokenId = _nextTokenId++;
        _mint(to, tokenId);
        _setTokenURI(tokenId, uri);

        tickets[tokenId] = TicketData({
            eventId: eventId,
            price: price,
            forSale: false,
            eventDate: eventDate,
            lastResaleTime: 0,
            used: false
        });

        emit TicketMinted(tokenId, to, eventId, price, eventDate);
    }

    /**
     * @notice List a ticket for resale
     * @param tokenId ID of the ticket to resell
     * @param price New resale price
     */
    function resellTicket(uint256 tokenId, uint256 price) public whenNotPaused {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        require(price >= MIN_RESALE_PRICE, "Price below minimum");
        
        TicketData storage ticket = tickets[tokenId];
        
        // Check if event has passed
        require(block.timestamp < ticket.eventDate, "Event has already occurred");
        
        // Check if ticket has been used
        require(!ticket.used, "Ticket has been used");
        
        // Cooldown period check
        require(
            ticket.lastResaleTime == 0 || 
            block.timestamp >= ticket.lastResaleTime + RESALE_COOLDOWN,
            "Resale cooldown active"
        );
        
        // Price validation: Check max multiplier
        uint256 maxPrice = ticket.price * MAX_RESALE_MULTIPLIER;
        require(price <= maxPrice, "Price exceeds max multiplier");

        ticket.price = price;
        ticket.forSale = true;
        ticket.lastResaleTime = block.timestamp;

        emit TicketListed(tokenId, price);
    }

    /**
     * @notice Buy a listed ticket
     * @param tokenId ID of the ticket to buy
     */
    function buyTicket(uint256 tokenId) public payable nonReentrant whenNotPaused {
        TicketData storage ticket = tickets[tokenId];
        
        // Check if ticket has been used (most critical check first)
        require(!ticket.used, "Ticket has been used");
        
        require(ticket.forSale, "Not for sale");
        require(msg.value >= ticket.price, "Insufficient funds");
        
        // Check if event has passed
        require(block.timestamp < ticket.eventDate, "Event has already occurred");
        
        // Rate limiting: Check buys per window
        uint256 currentWindow = block.timestamp / RATE_LIMIT_WINDOW;
        if (lastBuyWindow[msg.sender] != currentWindow) {
            buyCount[msg.sender] = 0;
            lastBuyWindow[msg.sender] = currentWindow;
        }
        require(buyCount[msg.sender] < MAX_BUYS_PER_BLOCK, "Rate limit exceeded");
        buyCount[msg.sender]++;

        address seller = ownerOf(tokenId);
        require(seller != msg.sender, "Cannot buy your own ticket");
        
        // Calculate refund if overpaid
        uint256 refundAmount = 0;
        if (msg.value > ticket.price) {
            refundAmount = msg.value - ticket.price;
        }
        
        // Transfer funds to seller (exact price)
        (bool sent, ) = payable(seller).call{value: ticket.price}("");
        require(sent, "Failed to send Ether to seller");

        // Refund overpayment to buyer
        if (refundAmount > 0) {
            (bool refundSent, ) = payable(msg.sender).call{value: refundAmount}("");
            require(refundSent, "Failed to refund overpayment");
        }

        // Transfer NFT
        _transfer(seller, msg.sender, tokenId);

        // Update state
        ticket.forSale = false;
        ticket.lastResaleTime = 0; // Reset cooldown on purchase
        
        emit TicketSold(tokenId, seller, msg.sender, ticket.price);
    }

    /**
     * @notice Validate a ticket (marks it as used)
     * @param tokenId ID of the ticket to validate
     */
    function validateTicket(uint256 tokenId) public onlyRole(VALIDATOR_ROLE) whenNotPaused {
        require(ownerOf(tokenId) != address(0), "Invalid token");
        require(!tickets[tokenId].used, "Ticket already used");
        
        tickets[tokenId].used = true;
        tickets[tokenId].forSale = false; // Cannot resell used tickets
        
        emit TicketValidated(tokenId, msg.sender);
    }

    /**
     * @notice Emergency pause function
     */
    function pause() public onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
        emit ContractPaused(msg.sender);
    }

    /**
     * @notice Unpause the contract
     */
    function unpause() public onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
        emit ContractUnpaused(msg.sender);
    }

    /**
     * @notice Withdraw contract balance (admin only)
     */
    function withdraw() public onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant {
        (bool sent, ) = payable(msg.sender).call{value: address(this).balance}("");
        require(sent, "Failed to withdraw");
    }

    /**
     * @notice Get ticket information
     * @param tokenId ID of the ticket
     * @return eventId Event ID
     * @return price Current price
     * @return forSale Whether ticket is for sale
     * @return eventDate Event date timestamp
     * @return used Whether ticket has been used
     */
    function getTicketInfo(uint256 tokenId) public view returns (
        uint256 eventId,
        uint256 price,
        bool forSale,
        uint256 eventDate,
        bool used
    ) {
        TicketData memory ticket = tickets[tokenId];
        return (
            ticket.eventId,
            ticket.price,
            ticket.forSale,
            ticket.eventDate,
            ticket.used
        );
    }

    // The following functions are overrides required by Solidity.

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721URIStorage, AccessControl, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}

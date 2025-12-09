// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";

contract NFTTicket is ERC721URIStorage, AccessControl, ReentrancyGuard, ERC2981 {
    uint256 private _nextTokenId;

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");

    struct TicketData {
        uint256 eventId;
        uint256 price;
        bool forSale;
    }

    mapping(uint256 => TicketData) public tickets;

    event TicketMinted(uint256 indexed tokenId, address indexed owner, uint256 eventId, uint256 price);
    event TicketListed(uint256 indexed tokenId, uint256 price);
    event TicketSold(uint256 indexed tokenId, address indexed from, address indexed to, uint256 price);
    event TicketValidated(uint256 indexed tokenId, address indexed validator);

    constructor() ERC721("NFTTicket", "NFTIX") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        
        // Set default royalty to 5% (500 basis points)
        _setDefaultRoyalty(msg.sender, 500);
    }

    function mintTicket(address to, string memory uri, uint256 eventId, uint256 price) public onlyRole(MINTER_ROLE) {
        uint256 tokenId = _nextTokenId++;
        _mint(to, tokenId);
        _setTokenURI(tokenId, uri);

        tickets[tokenId] = TicketData({
            eventId: eventId,
            price: price,
            forSale: false
        });

        emit TicketMinted(tokenId, to, eventId, price);
    }

    function resellTicket(uint256 tokenId, uint256 price) public {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        require(price > 0, "Price must be > 0");

        tickets[tokenId].price = price;
        tickets[tokenId].forSale = true;

        emit TicketListed(tokenId, price);
    }

    function buyTicket(uint256 tokenId) public payable nonReentrant {
        TicketData storage ticket = tickets[tokenId];
        require(ticket.forSale, "Not for sale");
        require(msg.value >= ticket.price, "Insufficient funds");

        address seller = ownerOf(tokenId);
        
        // Transfer funds to seller
        (bool sent, ) = payable(seller).call{value: msg.value}("");
        require(sent, "Failed to send Ether");

        // Transfer NFT
        _transfer(seller, msg.sender, tokenId);

        // Update state
        ticket.forSale = false;
        
        emit TicketSold(tokenId, seller, msg.sender, ticket.price);
    }

    function validateTicket(uint256 tokenId) public onlyRole(VALIDATOR_ROLE) {
        require(ownerOf(tokenId) != address(0), "Invalid token");
        emit TicketValidated(tokenId, msg.sender);
    }

    function withdraw() public onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant {
        (bool sent, ) = payable(msg.sender).call{value: address(this).balance}("");
        require(sent, "Failed to withdraw");
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

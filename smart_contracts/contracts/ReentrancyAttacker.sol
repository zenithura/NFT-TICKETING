// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./NFTTicket.sol";

/**
 * @title ReentrancyAttacker
 * @notice Test contract to verify reentrancy protection in NFTTicket
 * This contract attempts to exploit reentrancy vulnerabilities
 */
contract ReentrancyAttacker {
    NFTTicket public nftTicket;
    bool public attacking;

    constructor(address _nftTicket) {
        nftTicket = NFTTicket(_nftTicket);
    }

    function resellTicket(uint256 tokenId, uint256 price) external {
        nftTicket.resellTicket(tokenId, price);
    }

    function attack(uint256 tokenId) external payable {
        attacking = true;
        // Try to call buyTicket recursively
        nftTicket.buyTicket{value: msg.value}(tokenId);
        attacking = false;
    }

    receive() external payable {
        if (attacking && address(nftTicket).balance > 0) {
            // Attempt reentrancy
            nftTicket.buyTicket{value: 0}(0);
        }
    }

    function onERC721Received(
        address,
        address,
        uint256,
        bytes calldata
    ) external pure returns (bytes4) {
        return this.onERC721Received.selector;
    }
}


const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("TicketManager", function () {
    let TicketManager;
    let ticketManager;
    let owner;
    let addr1;
    let addr2;
    let addrs;

    beforeEach(async function () {
        [owner, addr1, addr2, ...addrs] = await ethers.getSigners();
        TicketManager = await ethers.getContractFactory("TicketManager");
        ticketManager = await TicketManager.deploy(owner.address, owner.address, 500);
    });

    describe("Deployment", function () {
        it("Should set the right admin", async function () {
            expect(await ticketManager.hasRole(await ticketManager.DEFAULT_ADMIN_ROLE(), owner.address)).to.equal(true);
        });
    });

    describe("Minting", function () {
        it("Should mint a new ticket", async function () {
            await ticketManager.mintTicket(addr1.address, 1, "ipfs://test");
            expect(await ticketManager.ownerOf(1)).to.equal(addr1.address);
        });
    });
});

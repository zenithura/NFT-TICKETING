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
        ticketManager = await TicketManager.deploy(owner.address, owner.address, 500); // 5% royalty
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

    describe("Listing", function () {
        beforeEach(async function () {
            await ticketManager.mintTicket(addr1.address, 1, "ipfs://test");
        });

        it("Should allow owner to list a ticket", async function () {
            await ticketManager.connect(addr1).listTicket(1, ethers.parseEther("1.0"));
            const listing = (await ticketManager.getTicketInfo(1)).listing;
            expect(listing.seller).to.equal(addr1.address);
            expect(listing.price).to.equal(ethers.parseEther("1.0"));
        });

        it("Should emit TicketListed event", async function () {
            await expect(ticketManager.connect(addr1).listTicket(1, ethers.parseEther("1.0")))
                .to.emit(ticketManager, "TicketListed")
                .withArgs(1, addr1.address, ethers.parseEther("1.0"));
        });

        it("Should not allow non-owner to list a ticket", async function () {
            await expect(ticketManager.connect(addr2).listTicket(1, ethers.parseEther("1.0")))
                .to.be.reverted; // Specific error message might depend on OpenZeppelin version or implementation details
        });
    });

    describe("Buying", function () {
        beforeEach(async function () {
            await ticketManager.mintTicket(addr1.address, 1, "ipfs://test");
            await ticketManager.connect(addr1).listTicket(1, ethers.parseEther("1.0"));
        });

        it("Should allow buyer to purchase a listed ticket", async function () {
            await ticketManager.connect(addr2).buyTicket(1, { value: ethers.parseEther("1.0") });
            expect(await ticketManager.ownerOf(1)).to.equal(addr2.address);
        });

        it("Should transfer funds to seller and royalty to recipient", async function () {
            const initialSellerBalance = await ethers.provider.getBalance(addr1.address);
            const initialRoyaltyBalance = await ethers.provider.getBalance(owner.address);

            await ticketManager.connect(addr2).buyTicket(1, { value: ethers.parseEther("1.0") });

            const finalSellerBalance = await ethers.provider.getBalance(addr1.address);
            const finalRoyaltyBalance = await ethers.provider.getBalance(owner.address);

            // 5% royalty = 0.05 ETH
            // Seller gets 0.95 ETH
            expect(finalRoyaltyBalance - initialRoyaltyBalance).to.equal(ethers.parseEther("0.05"));
            expect(finalSellerBalance - initialSellerBalance).to.equal(ethers.parseEther("0.95"));
        });

        it("Should emit TicketSold event", async function () {
            await expect(ticketManager.connect(addr2).buyTicket(1, { value: ethers.parseEther("1.0") }))
                .to.emit(ticketManager, "TicketSold")
                .withArgs(1, addr2.address, ethers.parseEther("1.0"));
        });
    });

    describe("Cancelling Listing", function () {
        beforeEach(async function () {
            await ticketManager.mintTicket(addr1.address, 1, "ipfs://test");
            await ticketManager.connect(addr1).listTicket(1, ethers.parseEther("1.0"));
        });

        it("Should allow seller to cancel listing", async function () {
            await ticketManager.connect(addr1).cancelListing(1);
            const listing = (await ticketManager.getTicketInfo(1)).listing;
            expect(listing.seller).to.equal(ethers.ZeroAddress);
        });

        it("Should emit TicketListingCancelled event", async function () {
            await expect(ticketManager.connect(addr1).cancelListing(1))
                .to.emit(ticketManager, "TicketListingCancelled")
                .withArgs(1);
        });
    });

    describe("Scanning", function () {
        beforeEach(async function () {
            await ticketManager.mintTicket(addr1.address, 1, "ipfs://test");
        });

        it("Should allow scanner to scan a ticket", async function () {
            await ticketManager.scanTicket(1);
            const info = (await ticketManager.getTicketInfo(1)).info;
            expect(info.scanned).to.equal(true);
        });

        it("Should emit TicketScanned event", async function () {
            await expect(ticketManager.scanTicket(1))
                .to.emit(ticketManager, "TicketScanned")
                .withArgs(1, owner.address);
        });

        it("Should not allow scanning twice", async function () {
            await ticketManager.scanTicket(1);
            await expect(ticketManager.scanTicket(1)).to.be.revertedWith("already scanned");
        });
    });

    describe("Royalties", function () {
        it("Should allow admin to set royalty", async function () {
            await ticketManager.setRoyalty(addr2.address, 1000); // 10%
            expect(await ticketManager.royaltyRecipient()).to.equal(addr2.address);
            expect(await ticketManager.royaltyBps()).to.equal(1000);
        });
    });
});

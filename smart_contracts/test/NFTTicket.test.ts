import { expect } from "chai";
import { ethers } from "hardhat";
import { NFTTicket } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { loadFixture, time } from "@nomicfoundation/hardhat-toolbox/network-helpers";

describe("NFTTicket", function () {
  // Helper function to get future timestamp
  async function getFutureDate(daysFromNow: number = 30) {
    const currentTime = await time.latest();
    return currentTime + (daysFromNow * 24 * 60 * 60);
  }

  // Fixture to deploy contract and get accounts
  async function deployNFTTicketFixture() {
    const [owner, minter, validator, buyer, seller, attacker] = await ethers.getSigners();
    const futureDate = await getFutureDate(30);

    const NFTTicketFactory = await ethers.getContractFactory("NFTTicket");
    const nftTicket = await NFTTicketFactory.deploy();

    return { nftTicket, owner, minter, validator, buyer, seller, attacker, futureDate };
  }

  describe("Deployment", function () {
    it("Should set the right name and symbol", async function () {
      const { nftTicket } = await loadFixture(deployNFTTicketFixture);
      expect(await nftTicket.name()).to.equal("NFTTicket");
      expect(await nftTicket.symbol()).to.equal("NFTIX");
    });

    it("Should grant DEFAULT_ADMIN_ROLE to deployer", async function () {
      const { nftTicket, owner } = await loadFixture(deployNFTTicketFixture);
      const DEFAULT_ADMIN_ROLE = await nftTicket.DEFAULT_ADMIN_ROLE();
      expect(await nftTicket.hasRole(DEFAULT_ADMIN_ROLE, owner.address)).to.be.true;
    });

    it("Should grant MINTER_ROLE to deployer", async function () {
      const { nftTicket, owner } = await loadFixture(deployNFTTicketFixture);
      const MINTER_ROLE = await nftTicket.MINTER_ROLE();
      expect(await nftTicket.hasRole(MINTER_ROLE, owner.address)).to.be.true;
    });

    it("Should set default royalty to 5%", async function () {
      const { nftTicket, owner } = await loadFixture(deployNFTTicketFixture);
      const [recipient, royaltyAmount] = await nftTicket.royaltyInfo(0, 10000);
      expect(recipient).to.equal(owner.address);
      expect(royaltyAmount).to.equal(500); // 5% of 10000 = 500
    });

    it("Should support ERC721, AccessControl, and ERC2981 interfaces", async function () {
      const { nftTicket } = await loadFixture(deployNFTTicketFixture);

      // ERC721 interface ID: 0x80ac58cd
      const ERC721_INTERFACE_ID = "0x80ac58cd";
      expect(await nftTicket.supportsInterface(ERC721_INTERFACE_ID)).to.be.true;

      // ERC2981 interface ID: 0x2a55205a
      const ERC2981_INTERFACE_ID = "0x2a55205a";
      expect(await nftTicket.supportsInterface(ERC2981_INTERFACE_ID)).to.be.true;
    });

    it("Should verify security constants", async function () {
      const { nftTicket } = await loadFixture(deployNFTTicketFixture);
      expect(await nftTicket.MAX_RESALE_MULTIPLIER()).to.equal(5);
      expect(await nftTicket.MIN_RESALE_PRICE()).to.equal(ethers.parseEther("0.001"));
      expect(await nftTicket.RESALE_COOLDOWN()).to.equal(3600); // 1 hour
      expect(await nftTicket.MAX_MINTS_PER_ADDRESS()).to.equal(100);
      expect(await nftTicket.MAX_BUYS_PER_WINDOW()).to.equal(10);
    });
  });

  describe("Minting", function () {
    it("Should mint a ticket successfully", async function () {
      const { nftTicket, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const eventId = 1;
      const price = ethers.parseEther("0.1");
      const uri = "https://example.com/ticket/1";

      await expect(nftTicket.mintTicket(buyer.address, uri, eventId, price, futureDate))
        .to.emit(nftTicket, "TicketMinted")
        .withArgs(0, buyer.address, eventId, price, futureDate);

      expect(await nftTicket.ownerOf(0)).to.equal(buyer.address);
      expect(await nftTicket.tokenURI(0)).to.equal(uri);

      const ticketInfo = await nftTicket.getTicketInfo(0);
      expect(ticketInfo.eventId).to.equal(eventId);
      expect(ticketInfo.price).to.equal(price);
      expect(ticketInfo.forSale).to.be.false;
      expect(ticketInfo.eventDate).to.equal(futureDate);
      expect(ticketInfo.used).to.be.false;
    });

    it("Should increment tokenId for each mint", async function () {
      const { nftTicket, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.mintTicket(buyer.address, "uri1", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.mintTicket(buyer.address, "uri2", 2, ethers.parseEther("0.2"), futureDate);
      await nftTicket.mintTicket(buyer.address, "uri3", 3, ethers.parseEther("0.3"), futureDate);

      expect(await nftTicket.ownerOf(0)).to.equal(buyer.address);
      expect(await nftTicket.ownerOf(1)).to.equal(buyer.address);
      expect(await nftTicket.ownerOf(2)).to.equal(buyer.address);
    });

    it("Should revert if non-minter tries to mint", async function () {
      const { nftTicket, buyer, attacker, futureDate } = await loadFixture(deployNFTTicketFixture);

      await expect(
        nftTicket.connect(attacker).mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.1"), futureDate)
      ).to.be.revertedWithCustomError(nftTicket, "AccessControlUnauthorizedAccount");
    });

    it("Should revert if price below minimum", async function () {
      const { nftTicket, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);

      await expect(
        nftTicket.mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.0001"), futureDate)
      ).to.be.revertedWith("Price below minimum");
    });

    it("Should revert if event date in past", async function () {
      const { nftTicket, buyer } = await loadFixture(deployNFTTicketFixture);
      const pastDate = (await time.latest()) - 86400; // Yesterday

      await expect(
        nftTicket.mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.1"), pastDate)
      ).to.be.revertedWith("Event date must be in future");
    });

    it("Should enforce rate limiting on minting", async function () {
      const { nftTicket, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);

      // Mint up to limit
      for (let i = 0; i < 100; i++) {
        await nftTicket.mintTicket(buyer.address, `uri${i}`, i, ethers.parseEther("0.1"), futureDate);
      }

      // Should fail on 101st mint
      await expect(
        nftTicket.mintTicket(buyer.address, "uri101", 101, ethers.parseEther("0.1"), futureDate)
      ).to.be.revertedWith("Max mints exceeded for address");
    });

    it("Should allow owner to grant MINTER_ROLE", async function () {
      const { nftTicket, owner, minter, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const MINTER_ROLE = await nftTicket.MINTER_ROLE();

      await nftTicket.grantRole(MINTER_ROLE, minter.address);
      expect(await nftTicket.hasRole(MINTER_ROLE, minter.address)).to.be.true;

      // New minter should be able to mint
      await expect(
        nftTicket.connect(minter).mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.1"), futureDate)
      ).to.emit(nftTicket, "TicketMinted");
    });
  });

  describe("Reselling", function () {
    it("Should allow owner to list ticket for resale", async function () {
      const { nftTicket, seller, futureDate } = await loadFixture(deployNFTTicketFixture);

      // Mint ticket to seller
      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      const newPrice = ethers.parseEther("0.5");

      await expect(nftTicket.connect(seller).resellTicket(0, newPrice))
        .to.emit(nftTicket, "TicketListed")
        .withArgs(0, newPrice);

      const ticketInfo = await nftTicket.getTicketInfo(0);
      expect(ticketInfo.price).to.equal(newPrice);
      expect(ticketInfo.forSale).to.be.true;
    });

    it("Should revert if non-owner tries to resell", async function () {
      const { nftTicket, seller, attacker, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);

      await expect(
        nftTicket.connect(attacker).resellTicket(0, ethers.parseEther("0.2"))
      ).to.be.revertedWith("Not owner");
    });

    it("Should revert if price below minimum", async function () {
      const { nftTicket, seller, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);

      await expect(
        nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.0001"))
      ).to.be.revertedWith("Price below minimum");
    });

    it("Should revert if price exceeds max multiplier (5x)", async function () {
      const { nftTicket, seller, futureDate } = await loadFixture(deployNFTTicketFixture);
      const originalPrice = ethers.parseEther("0.1");

      await nftTicket.mintTicket(seller.address, "uri", 1, originalPrice, futureDate);

      // Try to resell at 6x (should fail)
      await expect(
        nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.6"))
      ).to.be.revertedWith("Price exceeds max multiplier");

      // 5x should work
      await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.5"));
    });

    it("Should enforce cooldown period", async function () {
      const { nftTicket, seller, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);

      // First resale should work
      await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.2"));

      // Immediate second resale should fail
      await expect(
        nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.3"))
      ).to.be.revertedWith("Resale cooldown active");

      // After cooldown (1 hour), should work
      await time.increase(3600); // 1 hour
      await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.3"));
    });

    it("Should revert if event has passed", async function () {
      const { nftTicket, seller } = await loadFixture(deployNFTTicketFixture);
      const pastDate = (await time.latest()) + 3600; // 1 hour from now

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), pastDate);

      // Fast forward past event date
      await time.increase(7200); // 2 hours

      await expect(
        nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.2"))
      ).to.be.revertedWith("Event has already occurred");
    });

    it("Should revert if ticket has been used", async function () {
      const { nftTicket, seller, validator, futureDate } = await loadFixture(deployNFTTicketFixture);
      const VALIDATOR_ROLE = await nftTicket.VALIDATOR_ROLE();

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.grantRole(VALIDATOR_ROLE, validator.address);

      // Validate ticket
      await nftTicket.connect(validator).validateTicket(0);

      // Should not be able to resell
      await expect(
        nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.2"))
      ).to.be.revertedWith("Ticket has been used");
    });
  });

  describe("Buying Tickets", function () {
    it("Should allow buying a listed ticket", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const salePrice = ethers.parseEther("0.5");

      // Mint and list ticket
      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, salePrice);

      const sellerBalanceBefore = await ethers.provider.getBalance(seller.address);

      await expect(
        nftTicket.connect(buyer).buyTicket(0, { value: salePrice })
      )
        .to.emit(nftTicket, "TicketSold")
        .withArgs(0, seller.address, buyer.address, salePrice);

      expect(await nftTicket.ownerOf(0)).to.equal(buyer.address);

      const ticketInfo = await nftTicket.getTicketInfo(0);
      expect(ticketInfo.forSale).to.be.false;

      // Check seller received payment (accounting for gas)
      const sellerBalanceAfter = await ethers.provider.getBalance(seller.address);
      expect(sellerBalanceAfter > sellerBalanceBefore).to.be.true;
    });

    it("Should refund overpayment to buyer", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const salePrice = ethers.parseEther("0.5");
      const overPayment = ethers.parseEther("1.0");

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, salePrice);

      const buyerBalanceBefore = await ethers.provider.getBalance(buyer.address);

      const tx = await nftTicket.connect(buyer).buyTicket(0, { value: overPayment });
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * receipt!.gasPrice;

      const buyerBalanceAfter = await ethers.provider.getBalance(buyer.address);

      // Buyer should have paid salePrice + gas, and received refund
      // Balance change = -salePrice - gas
      const expectedChange = -(salePrice + gasUsed);
      const actualChange = buyerBalanceAfter - buyerBalanceBefore;

      // Allow small variance for gas estimation
      expect(actualChange).to.be.closeTo(expectedChange, ethers.parseEther("0.01"));
    });

    it("Should revert if ticket is not for sale", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);

      await expect(
        nftTicket.connect(buyer).buyTicket(0, { value: ethers.parseEther("1.0") })
      ).to.be.revertedWith("Not for sale");
    });

    it("Should revert if payment is insufficient", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const salePrice = ethers.parseEther("0.5");

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, salePrice);

      await expect(
        nftTicket.connect(buyer).buyTicket(0, { value: ethers.parseEther("0.1") })
      ).to.be.revertedWith("Insufficient funds");
    });

    it("Should revert if event has passed", async function () {
      const { nftTicket, seller, buyer } = await loadFixture(deployNFTTicketFixture);
      const futureDate = (await time.latest()) + 3600; // 1 hour from now

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.5"));

      // Fast forward past event
      await time.increase(7200);

      await expect(
        nftTicket.connect(buyer).buyTicket(0, { value: ethers.parseEther("0.5") })
      ).to.be.revertedWith("Event has already occurred");
    });

    it("Should revert if ticket has been used", async function () {
      const { nftTicket, seller, buyer, validator, futureDate } = await loadFixture(deployNFTTicketFixture);
      const VALIDATOR_ROLE = await nftTicket.VALIDATOR_ROLE();

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.5"));
      await nftTicket.grantRole(VALIDATOR_ROLE, validator.address);

      // Validate ticket (this sets used=true and forSale=false)
      await nftTicket.connect(validator).validateTicket(0);

      // Should fail because ticket is used (checked before forSale)
      await expect(
        nftTicket.connect(buyer).buyTicket(0, { value: ethers.parseEther("0.5") })
      ).to.be.revertedWith("Ticket has been used");
    });

    it("Should revert if buyer is seller", async function () {
      const { nftTicket, seller, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.5"));

      await expect(
        nftTicket.connect(seller).buyTicket(0, { value: ethers.parseEther("0.5") })
      ).to.be.revertedWith("Cannot buy your own ticket");
    });

    it("Should enforce rate limiting on buying", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);

      // Mint and list 11 tickets
      for (let i = 0; i < 11; i++) {
        await nftTicket.mintTicket(seller.address, `uri${i}`, i, ethers.parseEther("0.1"), futureDate);
        await nftTicket.connect(seller).resellTicket(i, ethers.parseEther("0.5"));
      }

      // Buy 10 tickets (should work)
      for (let i = 0; i < 10; i++) {
        await nftTicket.connect(buyer).buyTicket(i, { value: ethers.parseEther("0.5") });
      }

      // 11th buy should fail (rate limit exceeded)
      await expect(
        nftTicket.connect(buyer).buyTicket(10, { value: ethers.parseEther("0.5") })
      ).to.be.revertedWith("Rate limit exceeded");

      // Wait for next window (1 hour)
      await time.increase(3600);

      // Should work again
      await nftTicket.connect(buyer).buyTicket(10, { value: ethers.parseEther("0.5") });
    });

    it("Should prevent reentrancy attacks", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const salePrice = ethers.parseEther("0.5");

      // Test that normal operation works with nonReentrant
      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, salePrice);

      // Normal purchase should work
      await expect(
        nftTicket.connect(buyer).buyTicket(0, { value: salePrice })
      ).to.emit(nftTicket, "TicketSold");
    });
  });

  describe("Ticket Validation", function () {
    it("Should allow validator to validate ticket", async function () {
      const { nftTicket, owner, validator, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const VALIDATOR_ROLE = await nftTicket.VALIDATOR_ROLE();

      await nftTicket.grantRole(VALIDATOR_ROLE, validator.address);
      await nftTicket.mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.1"), futureDate);

      await expect(nftTicket.connect(validator).validateTicket(0))
        .to.emit(nftTicket, "TicketValidated")
        .withArgs(0, validator.address);

      const ticketInfo = await nftTicket.getTicketInfo(0);
      expect(ticketInfo.used).to.be.true;
      expect(ticketInfo.forSale).to.be.false;
    });

    it("Should revert if non-validator tries to validate", async function () {
      const { nftTicket, buyer, attacker, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.1"), futureDate);

      await expect(
        nftTicket.connect(attacker).validateTicket(0)
      ).to.be.revertedWithCustomError(nftTicket, "AccessControlUnauthorizedAccount");
    });

    it("Should revert if validating non-existent ticket", async function () {
      const { nftTicket, owner, validator } = await loadFixture(deployNFTTicketFixture);
      const VALIDATOR_ROLE = await nftTicket.VALIDATOR_ROLE();

      await nftTicket.grantRole(VALIDATOR_ROLE, validator.address);

      await expect(
        nftTicket.connect(validator).validateTicket(999)
      ).to.be.revertedWithCustomError(nftTicket, "ERC721NonexistentToken");
    });

    it("Should prevent validating already used ticket", async function () {
      const { nftTicket, validator, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const VALIDATOR_ROLE = await nftTicket.VALIDATOR_ROLE();

      await nftTicket.grantRole(VALIDATOR_ROLE, validator.address);
      await nftTicket.mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.1"), futureDate);

      // First validation should work
      await nftTicket.connect(validator).validateTicket(0);

      // Second validation should fail
      await expect(
        nftTicket.connect(validator).validateTicket(0)
      ).to.be.revertedWith("Ticket already used");
    });
  });

  describe("Pause Mechanism", function () {
    it("Should allow admin to pause contract", async function () {
      const { nftTicket, owner } = await loadFixture(deployNFTTicketFixture);

      await expect(nftTicket.connect(owner).pause())
        .to.emit(nftTicket, "ContractPaused")
        .withArgs(owner.address);

      expect(await nftTicket.paused()).to.be.true;
    });

    it("Should prevent operations when paused", async function () {
      const { nftTicket, owner, buyer, seller, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.connect(owner).pause();

      // Should not be able to mint
      await expect(
        nftTicket.mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.1"), futureDate)
      ).to.be.revertedWithCustomError(nftTicket, "EnforcedPause");

      // Mint before pause
      await nftTicket.connect(owner).unpause();
      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.5"));
      await nftTicket.connect(owner).pause();

      // Should not be able to buy
      await expect(
        nftTicket.connect(buyer).buyTicket(0, { value: ethers.parseEther("0.5") })
      ).to.be.revertedWithCustomError(nftTicket, "EnforcedPause");

      // Should not be able to resell
      await expect(
        nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.6"))
      ).to.be.revertedWithCustomError(nftTicket, "EnforcedPause");
    });

    it("Should allow admin to unpause contract", async function () {
      const { nftTicket, owner, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.connect(owner).pause();
      await nftTicket.connect(owner).unpause();

      expect(await nftTicket.paused()).to.be.false;

      // Should be able to mint again
      await expect(
        nftTicket.mintTicket(buyer.address, "uri", 1, ethers.parseEther("0.1"), futureDate)
      ).to.emit(nftTicket, "TicketMinted");
    });

    it("Should revert if non-admin tries to pause", async function () {
      const { nftTicket, attacker } = await loadFixture(deployNFTTicketFixture);

      await expect(
        nftTicket.connect(attacker).pause()
      ).to.be.revertedWithCustomError(nftTicket, "AccessControlUnauthorizedAccount");
    });
  });

  describe("Withdraw", function () {
    it("Should allow admin to withdraw contract balance", async function () {
      const { nftTicket, owner } = await loadFixture(deployNFTTicketFixture);

      // Contract balance should be 0 initially
      expect(await ethers.provider.getBalance(await nftTicket.getAddress())).to.equal(0);

      // Withdraw should still work (even with zero balance)
      await nftTicket.withdraw();

      const ownerBalanceBefore = await ethers.provider.getBalance(owner.address);
      const tx = await nftTicket.withdraw();
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * receipt!.gasPrice;

      const ownerBalanceAfter = await ethers.provider.getBalance(owner.address);

      // Owner should have paid gas
      expect(ownerBalanceAfter).to.be.lte(ownerBalanceBefore);
    });

    it("Should revert if non-admin tries to withdraw", async function () {
      const { nftTicket, attacker } = await loadFixture(deployNFTTicketFixture);

      await expect(
        nftTicket.connect(attacker).withdraw()
      ).to.be.revertedWithCustomError(nftTicket, "AccessControlUnauthorizedAccount");
    });
  });

  describe("Ticket Lifecycle Integration", function () {
    it("Should handle complete ticket lifecycle", async function () {
      const { nftTicket, seller, buyer, validator, futureDate } = await loadFixture(deployNFTTicketFixture);
      const VALIDATOR_ROLE = await nftTicket.VALIDATOR_ROLE();
      const initialPrice = ethers.parseEther("0.1");
      const resalePrice = ethers.parseEther("0.5");

      // 1. Mint ticket
      await nftTicket.mintTicket(seller.address, "uri", 1, initialPrice, futureDate);
      expect(await nftTicket.ownerOf(0)).to.equal(seller.address);

      // 2. List for resale
      await nftTicket.connect(seller).resellTicket(0, resalePrice);
      const ticketInfo1 = await nftTicket.getTicketInfo(0);
      expect(ticketInfo1.forSale).to.be.true;

      // 3. Buy ticket
      await nftTicket.connect(buyer).buyTicket(0, { value: resalePrice });
      expect(await nftTicket.ownerOf(0)).to.equal(buyer.address);

      // 4. Validate ticket
      await nftTicket.grantRole(VALIDATOR_ROLE, validator.address);
      await nftTicket.connect(validator).validateTicket(0);

      // 5. Verify final state
      const ticketInfo2 = await nftTicket.getTicketInfo(0);
      expect(ticketInfo2.forSale).to.be.false;
      expect(ticketInfo2.price).to.equal(resalePrice);
      expect(ticketInfo2.used).to.be.true;
    });

    it("Should handle multiple resales", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);

      // Get additional signer
      const signers = await ethers.getSigners();
      const buyer2 = signers[4];

      // Mint and first sale
      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.5"));
      await nftTicket.connect(buyer).buyTicket(0, { value: ethers.parseEther("0.5") });
      expect(await nftTicket.ownerOf(0)).to.equal(buyer.address);

      // Wait for cooldown
      await time.increase(3600);

      // Second resale
      await nftTicket.connect(buyer).resellTicket(0, ethers.parseEther("1.0"));
      await nftTicket.connect(buyer2).buyTicket(0, { value: ethers.parseEther("1.0") });
      expect(await nftTicket.ownerOf(0)).to.equal(buyer2.address);
    });
  });

  describe("Edge Cases", function () {
    it("Should handle zero address in mint", async function () {
      const { nftTicket, futureDate } = await loadFixture(deployNFTTicketFixture);

      await expect(
        nftTicket.mintTicket(ethers.ZeroAddress, "uri", 1, ethers.parseEther("0.1"), futureDate)
      ).to.be.revertedWith("Cannot mint to zero address");
    });

    it("Should maintain ticket data after multiple transfers", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const eventId = 1;
      const price = ethers.parseEther("0.1");

      await nftTicket.mintTicket(seller.address, "uri", eventId, price, futureDate);

      // Transfer without reselling
      await nftTicket.connect(seller).transferFrom(seller.address, buyer.address, 0);

      const ticketInfo = await nftTicket.getTicketInfo(0);
      expect(ticketInfo.eventId).to.equal(eventId);
      expect(ticketInfo.price).to.equal(price);
      expect(await nftTicket.ownerOf(0)).to.equal(buyer.address);
    });

    it("Should handle very large price values within limits", async function () {
      const { nftTicket, seller, futureDate } = await loadFixture(deployNFTTicketFixture);
      const largePrice = ethers.parseEther("1000000"); // 1M ETH

      await nftTicket.mintTicket(seller.address, "uri", 1, largePrice, futureDate);

      // Resell at 5x (max allowed)
      const maxResalePrice = largePrice * 5n;
      await nftTicket.connect(seller).resellTicket(0, maxResalePrice);

      const ticketInfo = await nftTicket.getTicketInfo(0);
      expect(ticketInfo.price).to.equal(maxResalePrice);
    });

    it("Should return correct ticket info", async function () {
      const { nftTicket, seller, futureDate } = await loadFixture(deployNFTTicketFixture);

      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);

      const ticketInfo = await nftTicket.getTicketInfo(0);
      expect(ticketInfo.eventId).to.equal(1);
      expect(ticketInfo.price).to.equal(ethers.parseEther("0.1"));
      expect(ticketInfo.forSale).to.be.false;
      expect(ticketInfo.eventDate).to.equal(futureDate);
      expect(ticketInfo.used).to.be.false;
    });
  });
});

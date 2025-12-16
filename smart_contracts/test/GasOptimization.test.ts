import { expect } from "chai";
import { ethers } from "hardhat";
import { NFTTicket } from "../typechain-types";
import { loadFixture, time } from "@nomicfoundation/hardhat-toolbox/network-helpers";

describe("Gas Optimization Tests", function () {
  async function getFutureDate(daysFromNow: number = 30) {
    const currentTime = await time.latest();
    return currentTime + (daysFromNow * 24 * 60 * 60);
  }

  async function deployNFTTicketFixture() {
    const [owner, minter, buyer, seller] = await ethers.getSigners();
    const futureDate = await getFutureDate(30);

    const NFTTicketFactory = await ethers.getContractFactory("NFTTicket");
    const nftTicket = await NFTTicketFactory.deploy();

    return { nftTicket, owner, minter, buyer, seller, futureDate };
  }

  describe("Gas Costs", function () {
    it("Should track gas for mintTicket", async function () {
      const { nftTicket, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      
      const tx = await nftTicket.mintTicket(
        buyer.address,
        "https://example.com/ticket/1",
        1,
        ethers.parseEther("0.1"),
        futureDate
      );
      const receipt = await tx.wait();
      
      // Gas should be reasonable (less than 250k)
      expect(receipt!.gasUsed).to.be.lt(250000n);
      console.log(`Mint gas used: ${receipt!.gasUsed.toString()}`);
    });

    it("Should track gas for resellTicket", async function () {
      const { nftTicket, seller, futureDate } = await loadFixture(deployNFTTicketFixture);
      
      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      
      const tx = await nftTicket.connect(seller).resellTicket(0, ethers.parseEther("0.5"));
      const receipt = await tx.wait();
      
      // Gas should be reasonable (less than 100k)
      expect(receipt!.gasUsed).to.be.lt(100000n);
      console.log(`Resell gas used: ${receipt!.gasUsed.toString()}`);
    });

    it("Should track gas for buyTicket", async function () {
      const { nftTicket, seller, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      const salePrice = ethers.parseEther("0.5");
      
      await nftTicket.mintTicket(seller.address, "uri", 1, ethers.parseEther("0.1"), futureDate);
      await nftTicket.connect(seller).resellTicket(0, salePrice);
      
      const tx = await nftTicket.connect(buyer).buyTicket(0, { value: salePrice });
      const receipt = await tx.wait();
      
      // Gas should be reasonable (less than 150k)
      expect(receipt!.gasUsed).to.be.lt(150000n);
      console.log(`Buy ticket gas used: ${receipt!.gasUsed.toString()}`);
    });

    it("Should track gas for batch minting", async function () {
      const { nftTicket, buyer, futureDate } = await loadFixture(deployNFTTicketFixture);
      
      // Mint 10 tickets
      const promises = [];
      for (let i = 0; i < 10; i++) {
        promises.push(
          nftTicket.mintTicket(
            buyer.address,
            `https://example.com/ticket/${i}`,
            i,
            ethers.parseEther("0.1"),
            futureDate
          )
        );
      }
      
      const txs = await Promise.all(promises);
      const receipts = await Promise.all(txs.map(tx => tx.wait()));
      
      const totalGas = receipts.reduce((sum, receipt) => sum + receipt!.gasUsed, 0n);
      const avgGas = totalGas / 10n;
      
      console.log(`Average gas per mint in batch: ${avgGas.toString()}`);
      expect(avgGas).to.be.lt(250000n);
    });
  });
});


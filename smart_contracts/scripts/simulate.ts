import { ethers } from "hardhat";

async function main() {
    const [owner, addr1] = await ethers.getSigners();
    const nftTicket = await ethers.getContractAt("NFTTicket", "0x5FbDB2315678afecb367f032d93F642f64180aa3");

    console.log("Minting ticket...");
    const tx = await nftTicket.mintTicket(addr1.address, "https://example.com/ticket/1", 1, ethers.parseEther("0.1"));
    await tx.wait();
    console.log("Ticket minted!");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

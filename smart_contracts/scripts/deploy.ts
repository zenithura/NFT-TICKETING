import { ethers } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();

    console.log("Deploying contracts with the account:", deployer.address);

    const nftTicket = await ethers.deployContract("NFTTicket");

    await nftTicket.waitForDeployment();

    console.log("NFTTicket deployed to:", await nftTicket.getAddress());
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

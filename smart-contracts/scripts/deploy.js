// File header: Hardhat deployment script for TicketManager smart contract.
// Deploys the contract to the configured network with admin and royalty settings.

const hre = require("hardhat");

// Purpose: Deploy TicketManager contract to blockchain network.
// Side effects: Deploys contract, sets deployer as admin and royalty recipient, configures 5% royalty.
async function main() {
    const [deployer] = await hre.ethers.getSigners();

    console.log("Deploying contracts with the account:", deployer.address);

    // Purpose: Get contract factory for TicketManager.
    // Side effects: Compiles contract if needed.
    const TicketManager = await hre.ethers.getContractFactory("TicketManager");
    // Purpose: Deploy contract with constructor parameters (admin, royalty recipient, 500 bps = 5%).
    // Side effects: Sends deployment transaction to blockchain.
    const ticketManager = await TicketManager.deploy(deployer.address, deployer.address, 500);

    await ticketManager.waitForDeployment();

    console.log("TicketManager deployed to:", await ticketManager.getAddress());
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

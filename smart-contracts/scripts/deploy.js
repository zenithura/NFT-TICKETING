const hre = require("hardhat");

async function main() {
    const [deployer] = await hre.ethers.getSigners();

    console.log("Deploying contracts with the account:", deployer.address);

    const TicketManager = await hre.ethers.getContractFactory("TicketManager");
    // Admin, Royalty Recipient, Royalty BPS (5%)
    const ticketManager = await TicketManager.deploy(deployer.address, deployer.address, 500);

    await ticketManager.waitForDeployment();

    console.log("TicketManager deployed to:", await ticketManager.getAddress());
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

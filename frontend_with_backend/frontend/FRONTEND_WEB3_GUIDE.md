# Frontend Web3 Integration Guide

## Setup Instructions

### 1. Install Dependencies
```bash
cd frontend_with_backend/frontend
npm install ethers@^6.0.0
```

### 2. Configure Environment Variables
Create `.env` file in the frontend directory:
```bash
REACT_APP_CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
REACT_APP_RPC_URL=http://127.0.0.1:8545
REACT_APP_API_URL=http://localhost:8000/api
```

### 3. Copy Contract Artifacts
The `web3Service.js` imports the contract ABI from Hardhat artifacts. Ensure the path is correct or copy the ABI:
```bash
# Option 1: Use relative path (already configured)
# The service imports from ../../../smart-contracts/artifacts/...

# Option 2: Copy ABI to frontend
cp smart-contracts/artifacts/contracts/TicketManager.sol/TicketManager.json \\
   frontend_with_backend/frontend/src/contracts/
```

## Created Files

### Core Service
- **[src/services/web3Service.js](file:///home/mahammad/NFT-TICKETING/frontend_with_backend/frontend/src/services/web3Service.js)** - Web3 interaction service

### React Components
- **[src/components/WalletConnect.jsx](file:///home/mahammad/NFT-TICKETING/frontend_with_backend/frontend/src/components/WalletConnect.jsx)** - Wallet connection UI
- **[src/components/MyTickets.jsx](file:///home/mahammad/NFT-TICKETING/frontend_with_backend/frontend/src/components/MyTickets.jsx)** - Ticket management UI

## Usage Example

```jsx
import React, { useState } from 'react';
import WalletConnect from './components/WalletConnect';
import MyTickets from './components/MyTickets';
import web3Service from './services/web3Service';

function App() {
  const [account, setAccount] = useState(null);

  useEffect(() => {
    const currentAccount = web3Service.getCurrentAccount();
    setAccount(currentAccount);
  }, []);

  return (
    <div className="App">
      <header>
        <WalletConnect />
      </header>
      <main>
        <MyTickets walletAddress={account} />
      </main>
    </div>
  );
}
```

## Features Implemented

✅ **Wallet Connection** - MetaMask integration
✅ **View Owned Tickets** - Query tickets from blockchain
✅ **List for Resale** - Create marketplace listings
✅ **Cancel Listings** - Remove from marketplace
✅ **Buy Tickets** - Purchase from marketplace
✅ **Account Change Detection** - Auto-refresh on wallet switch

## Next Steps

1. **Integrate with existing UI** - Add components to current pages
2. **Sync with Backend** - Combine on-chain data with database info
3. **Add Loading States** - Better UX during transactions
4. **Error Handling** - User-friendly error messages
5. **Transaction Notifications** - Toast notifications for tx status
6. **IPFS Metadata** - Display ticket images and details from IPFS

## Testing

1. **Install MetaMask** browser extension
2. **Add Hardhat Network** to MetaMask:
   - Network Name: Hardhat Local
   - RPC URL: http://127.0.0.1:8545
   - Chain ID: 1337
   - Currency: ETH
3. **Import Test Account** using private key from Hardhat
4. **Connect Wallet** and test functionality

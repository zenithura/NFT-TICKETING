# API Implementation Summary

This document outlines the APIs implemented to support the requested functionalities: Mint Ticket, List Ticket, Buy Ticket, and Add Validator.

## 1. Mint Ticket
**Functionality**: Mints a new NFT ticket for an event.
**Files Modified**:
- `frontend_with_backend/backend/server.py`: Updated `mint_ticket` endpoint.
- `frontend_with_backend/backend/blockchain.py`: Updated `mint_ticket` method.
- `frontend_with_backend/backend/add_blockchain_id.sql`: Added `blockchain_id` column to `tickets` table.

**Implementation Details**:
- The `mint_ticket` API now calls the blockchain service to mint the token on-chain.
- It retrieves the on-chain `tokenId` from the transaction logs and stores it in the `tickets` table (column `blockchain_id`) for future reference.

## 2. List Ticket
**Functionality**: Lists a ticket for resale.
**Files Modified**:
- `frontend_with_backend/backend/server.py`: Updated `list_resale` endpoint.
- `frontend_with_backend/backend/blockchain.py`: Added `list_ticket` method.

**Implementation Details**:
- The `list_resale` API now attempts to call `listTicket` on the smart contract.
- **Note**: This operation requires the caller (Server) to be the owner or approved operator of the token. If the user holds the token in a non-custodial wallet, this on-chain call will fail unless the user has approved the server.

## 3. Buy Ticket
**Functionality**: Purchases a listed ticket.
**Files Modified**:
- `frontend_with_backend/backend/server.py`: Updated `buy_resale` endpoint.
- `frontend_with_backend/backend/blockchain.py`: Added `buy_ticket` method.

**Implementation Details**:
- The `buy_resale` API now attempts to call `buyTicket` on the smart contract.
- **Note**: This operation requires sending ETH (`msg.value`). The server wallet must have sufficient funds if it is executing this transaction.

## 4. Add Validator (Scanner)
**Functionality**: Registers a new scanner/validator for an event venue.
**Files Modified**:
- `frontend_with_backend/backend/server.py`: Updated `register_scanner` endpoint.
- `frontend_with_backend/backend/blockchain.py`: Added `grant_scanner_role` method.

**Implementation Details**:
- The `register_scanner` API now calls `grant_scanner_role` on the blockchain to grant the `SCANNER_ROLE` to the operator's wallet address.

## Database Changes
A migration file `frontend_with_backend/backend/add_blockchain_id.sql` was created to add the `blockchain_id` column to the `tickets` table.
A script `frontend_with_backend/backend/apply_migration.py` is provided to apply this migration if needed.

## Files
- [server.py](frontend_with_backend/backend/server.py)
- [blockchain.py](frontend_with_backend/backend/blockchain.py)
- [add_blockchain_id.sql](frontend_with_backend/backend/add_blockchain_id.sql)

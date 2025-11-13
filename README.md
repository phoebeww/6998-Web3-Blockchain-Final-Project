# Distributed Voting System

A minimal blockchain-based voting system demonstrating transactions, block mining, and chain validation.

## Overview

The Distributed Voting System aims to provide a secure and verifiable framework for digital voting using blockchain technology. The full system is designed to support decentralized participation, cryptographic verification, and multi-node consensus.

### Key Features

- Immutable vote recording through Proof-of-Work (PoW)
- Prevention of duplicate voting by voter ID
- Block and chain validation
- Text-based results visualization

### How it works

- Transaction – represents a single vote (`voter_id`, `choice`, `timestamp`)
- Block – groups transactions and links to the previous block via hash
- Proof-of-Work – ensures each new block meets the required hash difficulty
- Validation – detects tampering and maintains chain integrity
- Double-vote prevention – blocks repeated votes from the same voter ID

## Project Structure

```
mvp_blockchain.py   # Core blockchain and Proof-of-Work implementation
mvp_voting.py       # Command-line voting interface
demo.py             # Automated demonstration script
 ```

## Quick Start

### Run the Automated Demo

```bash
python demo.py
```

#### which includes:

- Creates a blockchain
- Adds sample votes
- Prevents duplicate voting
- Mines two blocks
- Displays results and verifies integrity

### Run the Interactive version:

```bash
python mvp_voting.py
```

#### which provides a simple system for:

- Submit votes
- Mine pending transactions
- View the blockchain
- Display vote results
- Verify chain validity

## Future Goals
Planned improvements beyond the MVP include:

- Adding persistent storage so the chain can be saved and reloaded
- Implementing Proof-of-Stake (PoS) or another consensus method
- Introducing basic networking to allow multiple nodes
- Adding digital signatures for voter authentication
- Building a simple web interface for easier interaction
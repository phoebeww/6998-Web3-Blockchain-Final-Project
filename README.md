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
core/
    blockchain.py   # Block, Transaction, Blockchain (PoW, validation, persistence)
    node.py         # Node wrapper (one blockchain + peer list + networking hooks)

api/
    server.py       # FastAPI HTTP server exposing node API

network/
    schemas.py      # Shared Pydantic models for nodes & message passing
    tracker.py      # Tracker service for node registration & peer discovery

data/
    chain_<node-id>.json  # Auto-generated chain files per node

 ```

## Quick Start

### Activate the virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\Activate         # Windows PowerShell
pip install -r requirements.txt
```

### Run the Tracker

```bash
uvicorn network.tracker:app --reload --port 9000
```

### Run a Node

```bash
uvicorn api.server:app --reload --port 8000
```
Note: `api/server.py` line 51, we run a single node in this process *right now*. We will run multiple processes with different node_ids/ports for full implementation.

#### Node endpoints:
- `POST /vote`
- `POST /mine`
- `GET /results`
- `GET /chain`
- `GET /stats`
- `GET /validate`
- `POST /message` (for P2P messages — not implemented yet)

## Testing (current version)

After running both tracker and node in different terminal, run the script:
```bash
chmod +x test_single_node_with_tracker.sh
./test_single_node_with_tracker.sh
```
**This is only based on SINGLE NODE.**

## TODO List

## Backend Networking

### Node Registration with Tracker
Files: `api/server.py`, `core/node.py`

- After node startup, call:
node.register_with_tracker("http://localhost:9000")
- Store returned peer list in self.peers.

### Implement `/message` endpoint logic
Files: `core/node.py`, `api/server.py`

Implement:
- Node.broadcast_block (block)
- Node.request_chain_from_peer (peer)
- Node.handle_incoming_message (message)

Message types:
- "NEW_BLOCK"
- "REQUEST_CHAIN"
- "CHAIN_RESPONSE"

### Consensus Rule (Longest Valid Chain Wins)
File: `core/node.py`

When receiving "CHAIN_RESPONSE":
1. Rebuild chain from message
2. Validate it
3. If longer + valid → replace local chain
4. Save to `data/chain_<node_id>.json`

### Trigger Broadcasting
File: `core/node.py`

After mining:
```
block = self.mine()
if block:
    self.broadcast_block(block)
```

## Front End UI

### Voting UI
- Form for voter_id + choice
- Calls `/vote`

### Results UI
- Table or bar chart
- Calls `/results`

### Block Explorer
- Calls `/chain`
- Shows blocks + transactions

### Node Status Bar
- Calls `/stats`
- Shows chain validity badge

### Multi-Node Demo
- Run UI twice, pointing to:
    - Node 1 URL
    - Node 2 URL
- Shows how nodes differ → later sync when consensus implemented.

## Optional
- Multi-node startup script (`scripts/start_network.py`)
- Improved PoW difficulty controls

**TODO items above are not determined and can be discussed later.**

# Distributed Voting System

A minimal blockchain-based voting system demonstrating transactions, block mining, peer-to-peer consensus, and chain validation.

## Overview

The Distributed Voting System aims to provide a secure and verifiable framework for digital voting using blockchain technology. The full system is designed to support decentralized participation, cryptographic verification, and multi-node consensus.

### Key Features

- **Decentralized UI:** Each node hosts its own frontend; no central server required.
- **Immutable vote recording:** Uses Proof-of-Work (PoW) to secure the chain.
- **Consensus Algorithm:** Nodes automatically sync to the longest valid chain.
- **Double-vote prevention:** Blocks repeated votes from the same voter ID.
- **Real-time Peer Discovery:** Nodes register with a tracker to find peers.

### How it works

- **Transaction** – represents a single vote (`voter_id`, `choice`, `timestamp`).
- **Block** – groups transactions and links to the previous block via hash.
- **Proof-of-Work** – ensures each new block meets the required hash difficulty.
- **Validation** – detects tampering and maintains chain integrity.
- **Broadcasting** – when a node mines a block, it broadcasts it to the network.

## Project Structure

```text
/
├── run_network.py      # Automation script to launch Tracker + 3 Nodes + Browser Tabs
├── core/
│   ├── blockchain.py   # Block, Transaction, Blockchain
│   └── node.py         # Node wrapper 
├── api/
│   ├── server.py       # FastAPI HTTP server exposing node API & serving UI
├── network/
│   ├── schemas.py      # Shared Pydantic models for nodes & message passing
│   └── tracker.py      # Tracker service for node registration & peer discovery
├── static/
│   └── index.html      # React-based Frontend (served by each node)
└── data/
    └── chain_<id>.json # Auto-generated chain files per node
```

## API Endpoints
Each node exposes the following API endpoints (accessible via `http://localhost:<port>/docs`):

- `POST /vote` - Submit a new vote (transaction).

- `POST /mine` - Trigger Proof-of-Work to seal pending votes.

- `GET /results` - Calculate current election tally.

- `GET /chain` - View the full blockchain history.

- `GET /stats` - View node connectivity and block count.

- `POST /message` - Internal P2P communication endpoint.

## Quick Start

### Activate the virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\Activate         # Windows PowerShell
pip install -r requirements.txt
```

### Run the Full Network (Recommended)
We have included an automation script that launches the Tracker and 3 Nodes simultaneously, and opens their dashboards in your browser.

```bash
python run_network.py
```

### Manual Startup (Alternative)
If you prefer running components manually, open separate terminals:

Terminal 1 (Tracker)
```bash
uvicorn network.tracker:app --port 9000
```

Terminal 2 (Node 1)
```bash
export NODE_ID=node-1
export NODE_PORT=8000
uvicorn api.server:app --port 8000
```
Repeat for Node 2 (Port 8002) and Node 3 (Port 8003).

## Testing The Consensus

The system simulates a "Mini Internet" on your localhost. Here is how to test the decentralized logic:

1. Launch the network (python run_network.py).

2. Vote on Node 1:
    - Go to the browser tab for Node 1 (port 8000).
    - Vote for "Alice" using ID "Voter1".
    - Go to the Mine tab and mine the block.

3. Verify Sync on Node 2:
    - Switch to the browser tab for Node 2 (port 8002).
    - Wait a few seconds.
    - You will see the block mined by Node 1 appear on Node 2's chain automatically.

4. Test New Node Sync:
    - The script launches a third node (Node 3) on port 8003.
    - Even though Node 3 came online after the others, it will automatically download the longest chain from its peers.

## TODO List

## Optional
- Multi-node startup script (`scripts/start_network.py`)
- Improved PoW difficulty controls

**TODO items above are not determined and can be discussed later.**

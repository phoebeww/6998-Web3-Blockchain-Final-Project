# Distributed Voting System

A blockchain-based voting system featuring dynamic difficulty adjustment, digital signatures, hybrid PoW+PoS consensus, and Merkle tree verification.

## Overview

The Distributed Voting System provides a secure and verifiable framework for digital voting using advanced blockchain technology. The system demonstrates decentralized participation, cryptographic verification, hybrid consensus mechanisms, and automatic network synchronization.

### Key Features

- **Hybrid Consensus:** Combines Proof-of-Work (PoW) security with Proof-of-Stake (PoS) efficiency through reputation-based staking.
- **Dynamic Difficulty Adjustment:** Automatically adjusts mining difficulty based on block production rate to maintain consistent block times.
- **Digital Signatures:** RSA-2048 cryptographic signatures ensure vote authenticity and prevent identity forgery.
- **Merkle Tree Verification:** Efficient transaction integrity verification using Merkle roots.
- **Stake-Based Mining:** Nodes earn reputation (stake) by mining blocks, which reduces their future mining difficulty.
- **Decentralized UI:** Each node hosts its own frontend with real-time updates.
- **Double-Vote Prevention:** Cryptographically enforced one-person-one-vote using public key hashing.
- **Automatic Peer Sync:** Nodes automatically discover peers and synchronize blockchain state.

### How it Works

#### Core Components

- **Transaction** – represents a single vote with digital signature (`voter_id`, `choice`, `timestamp`, `signature`, `public_key`, `username`).
- **Block** – groups transactions with cryptographic linkage (`hash`, `previous_hash`, `merkle_root`, `miner_id`, `stake`, `difficulty`).
- **Proof-of-Work** – ensures computational cost to create blocks, preventing rapid block creation.
- **Proof-of-Stake** – rewards honest miners with stake points that reduce their mining difficulty.
- **Dynamic Difficulty** – adjusts base difficulty every 3 blocks based on average block production time.
- **Merkle Tree** – provides efficient verification that transactions haven't been tampered with.

#### Consensus Mechanism

The system uses a **hybrid PoW + PoS consensus**:

1. **Base Difficulty (PoW)** - Adjusted based on network block production rate:
   - If avg block time < 15s → Increase difficulty
   - If avg block time > 20s → Decrease difficulty
   - Target: 17.5 seconds per block

2. **Stake Bonus (PoS)** - Miners earn reputation through successful mining:
   - Each successful block → +1 stake
   - Every 7 stake points → -1 mining difficulty (max -2)
   - Higher stake → Easier mining → More blocks → Higher stake (positive feedback)

3. **Final Mining Difficulty** = Base Difficulty - Stake Bonus

Example: If base difficulty is 4 and a node has 14 stake:
- Stake bonus = 14 // 7 = 2
- Mining difficulty = 4 - 2 = 2
- This node mines faster than nodes with lower stake

## Project Structure

```text
/
├── config.py           # System configuration (difficulty, stake, timing parameters)
├── run_network.py      # Automation script to launch Tracker + 3 Nodes + Browser Tabs
├── requirements.txt    # Python dependencies (FastAPI, cryptography, etc.)
├── core/
│   ├── blockchain.py   # Block, Transaction, Blockchain with Merkle trees
│   ├── node.py         # Node with stake management and difficulty calculation
│   └── crypto.py       # RSA key generation, signing, and verification
├── api/
│   └── server.py       # FastAPI HTTP server with REST API & UI serving
├── network/
│   ├── schemas.py      # Pydantic models for P2P messages
│   └── tracker.py      # Tracker with stake leaderboard management
├── static/
│   └── index.html      # React-based Frontend with real-time updates
└── data/
    ├── chain_<id>.json # Blockchain persistence per node
    └── stake_<id>.json # Stake persistence per node
```

## API Endpoints

Each node exposes the following API endpoints (accessible via `http://localhost:<port>/docs`):

### Voting & Keys
- `GET /generate_keys` - Generate a new RSA-2048 keypair for voting
- `POST /vote` - Submit a vote (legacy, unsigned)
- `POST /vote_signed` - Submit a cryptographically signed vote with optional username

### Mining & Blockchain
- `POST /mine` - Trigger Proof-of-Work mining with stake-adjusted difficulty
- `GET /chain` - View the full blockchain with all blocks and transactions
- `GET /validate` - Validate the entire blockchain including Merkle roots

### Statistics & Monitoring
- `GET /stats` - Node stats including difficulty, stake, and mining advantage
- `GET /results` - Current election results with vote counts and percentages
- `GET /config` - System configuration parameters (difficulty thresholds, stake settings)

### Network & Stake
- `GET /stakes` - Get the network-wide stake leaderboard from tracker
- `POST /message` - Internal P2P communication endpoint for block propagation

### Tracker Endpoints (Port 9000)
- `POST /register` - Node registration and peer discovery
- `GET /peers` - List all active peers
- `POST /update_stake` - Node reports stake updates
- `GET /stakes` - Get global stake leaderboard

## Quick Start

### Prerequisites
- Python 3.7 or higher
- pip package manager
- Modern web browser (Chrome, Firefox, Safari, or Edge)

### Installation

1. **Create and activate virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\Activate         # Windows PowerShell
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `requests` - HTTP client
- `cryptography` - RSA signature support

### Run the Full Network (Recommended)

We have included an automation script that launches the Tracker and 3 Nodes simultaneously, and opens their dashboards in your browser.

```bash
python run_network.py
```

The script will:
1. Start Tracker on port 9000
2. Start Node-1 on port 8000
3. Start Node-2 on port 8001
4. Start Node-3 on port 8002
5. Open browser tabs for all three nodes

### Manual Startup (Alternative)

If you prefer running components manually, open separate terminals:

**Terminal 1 (Tracker):**
```bash
uvicorn network.tracker:app --port 9000
```

**Terminal 2 (Node 1):**
```bash
export NODE_ID=node-1
export NODE_PORT=8000
uvicorn api.server:app --port 8000
# Then open http://localhost:8000 in browser
```

**Terminal 3 (Node 2):**
```bash
export NODE_ID=node-2
export NODE_PORT=8001
uvicorn api.server:app --port 8001
# Then open http://localhost:8001 in browser
```

**Terminal 4 (Node 3):**
```bash
export NODE_ID=node-3
export NODE_PORT=8002
uvicorn api.server:app --port 8002
# Then open http://localhost:8002 in browser
```

## Testing The System

The system simulates a decentralized network on localhost. Here are comprehensive test scenarios:

### Test 1: Digital Signature Voting

1. **Launch the network:**
   ```bash
   python run_network.py
   ```

2. **Generate voting keys (Node 1 - http://localhost:8000):**
   - Navigate to the **Vote** tab
   - Click **"Generate Keys"**
   - You'll see your Voter ID (derived from public key hash)
   - Your keys are stored locally in browser localStorage

3. **Cast a signed vote:**
   - Enter a display name (e.g., "Alice Smith") - optional
   - Select a candidate (e.g., "Bob")
   - Click **"Submit Signed Vote"**
   - After success alert, keys are auto-deleted (one key = one vote)

4. **Mine the block:**
   - Navigate to the **Mine** tab
   - Observe your mining advantage panel (shows stake and difficulty)
   - Click **"Mine New Block"**
   - Watch the proof-of-work process

5. **View results:**
   - Go to **Results** tab to see vote tallies
   - Go to **Dashboard** to see blockchain with Merkle roots

### Test 2: Dynamic Difficulty Adjustment

1. **Fast mining scenario:**
   - Vote and mine blocks rapidly (< 15 seconds apart)
   - Observe **Dashboard → Dynamic Difficulty Monitor**
   - Base difficulty should increase (2 → 3 → 4...)
   - Status shows "Mining too fast! Difficulty will increase"

2. **Slow mining scenario:**
   - Wait 20+ seconds between blocks
   - Base difficulty should decrease
   - Status shows "Mining too slow! Difficulty has decreased"

3. **Optimal range:**
   - Mine blocks 15-20 seconds apart
   - Difficulty remains stable
   - Status shows "Mining speed is optimal"

### Test 3: Stake-Based Consensus

1. **Accumulate stake on Node 1:**
   - Vote and mine 7 blocks on Node 1
   - Observe **Dashboard → Your Stake** card: should show ⭐7
   - Check **Mine tab → Your Mining Advantage**:
     - Your Stake: 7
     - Base Difficulty: 3 (example)
     - Your Difficulty: 2 (one less due to stake bonus)

2. **Compare with Node 2:**
   - Open Node 2 (http://localhost:8001)
   - Mine 3 blocks on Node 2
   - Node 2 stake: 3, no bonus yet
   - Node 1 should mine faster due to lower difficulty

3. **View stake leaderboard:**
   - Check **Dashboard → Node Reputation Leaderboard**
   - See all nodes ranked by stake
   - Mining advantage displayed for each node

### Test 4: Multi-Node Synchronization

1. **Mine on Node 1:**
   - Create and mine a block on Node 1

2. **Auto-sync to Node 2 and 3:**
   - Switch to Node 2 (http://localhost:8001)
   - Wait a few seconds
   - The new block appears automatically
   - **Base difficulty is synchronized** across all nodes
   - Merkle root is identical

3. **Late-joining node:**
   - Node 3 starts after others
   - Automatically downloads the longest chain
   - Syncs base_difficulty from the chain
   - All nodes converge to the same state

### Test 5: Security Features

1. **Double-vote prevention:**
   - Generate keys and vote
   - Try to vote again with same keys
   - Should show error: "duplicate_voter"

2. **Signature verification:**
   - All votes in mined blocks show "✓ Signed" status
   - Tampering with transaction data would break Merkle verification

3. **Chain validation:**
   - Navigate to `http://localhost:8000/validate`
   - Should return `{"valid": true}`
   - Merkle roots are verified as part of validation

### Test 6: Stake Persistence

1. **Mine several blocks** to accumulate stake (e.g., 10 blocks → 10 stake)

2. **Restart the network:**
   ```bash
   # Press Ctrl+C to stop
   python run_network.py
   ```

3. **Verify stake persisted:**
   - Open any node's dashboard
   - Stake value should be preserved (not reset to 0)
   - Mining difficulty advantage remains

## Configuration

The system behavior can be customized by editing `config.py`:

### Mining Configuration
```python
BASE_DIFFICULTY = 2              # Initial difficulty level
MIN_DIFFICULTY = 1               # Minimum allowed difficulty
MAX_DIFFICULTY = 5               # Maximum allowed difficulty
TARGET_BLOCK_TIME = 17.5         # Target seconds between blocks
DIFFICULTY_ADJUSTMENT_INTERVAL = 3  # Blocks before adjusting difficulty
DIFFICULTY_INCREASE_THRESHOLD = 15  # Increase difficulty if avg < 20s
DIFFICULTY_DECREASE_THRESHOLD = 20  # Decrease difficulty if avg > 30s
```

### Stake Configuration
```python
DEFAULT_STAKE = 0                # Initial stake for new nodes
STAKE_REWARD = 1                 # Stake earned per successfully mined block
STAKE_PENALTY = 2                # Penalty for invalid blocks (reserved)
MAX_STAKE_INFLUENCE = 2          # Maximum difficulty reduction from stake
```

### How Stake Works
- Mining difficulty = Base Difficulty - (Stake // 7)
- Every 7 stake points reduces difficulty by 1
- Maximum reduction: 2 difficulty levels
- Example:
  - Stake 0-6: No bonus
  - Stake 7-13: -1 difficulty
  - Stake 14+: -2 difficulty (max)

## Architecture Details

### Consensus Flow

```
1. Dynamic Difficulty Adjustment (PoW)
   └─ Analyze last 3 blocks' timestamps
   └─ Calculate average block time
   └─ Adjust base_difficulty if needed
   └─ Broadcast in next block's base_difficulty field

2. Stake Calculation (PoS)
   └─ Node loads persisted stake value
   └─ Calculates stake bonus (stake // 7)
   └─ Determines mining difficulty = base - bonus

3. Block Creation
   └─ Package pending transactions
   └─ Calculate Merkle root of transactions
   └─ Record: miner_id, stake, base_difficulty, difficulty
   └─ Perform PoW with adjusted difficulty

4. Block Propagation
   └─ Broadcast to all peers via P2P messages
   └─ Peers validate: PoW, signatures, Merkle root
   └─ Peers sync base_difficulty from block
   └─ Update miner's stake in tracker

5. Consensus Resolution
   └─ If fork detected: longest valid chain wins
   └─ All nodes converge to same base_difficulty
   └─ Each node maintains independent stake
```

### Transaction Lifecycle

```
1. User generates RSA keypair (2048-bit)
   └─ Private key stored in browser localStorage
   └─ Public key hashed to create voter_id

2. User casts vote
   └─ Chooses candidate
   └─ Optionally provides display name
   └─ Transaction signed with private key

3. Node validates
   └─ Verify signature with public key
   └─ Check voter_id not in chain (no double-voting)
   └─ Add to pending transaction pool

4. Mining packages transactions
   └─ Calculate Merkle root of all pending transactions
   └─ Include in block header
   └─ Perform PoW with stake-adjusted difficulty

5. Block propagated and verified
   └─ Other nodes check Merkle root validity
   └─ Verify all signatures
   └─ Add to local chain if valid
```

### Security Model

#### Layer 1: Identity Security
- **RSA-2048 Digital Signatures:** Each vote cryptographically signed
- **Public Key Hashing:** Voter IDs derived from public keys (first 16 hex chars)
- **One-Key-One-Vote:** Keys auto-deleted after voting
- **Signature Verification:** All transactions verified before inclusion

#### Layer 2: Block Security
- **Proof-of-Work:** Computational puzzle prevents rapid block creation
- **Hash Chaining:** Each block links to previous via cryptographic hash
- **Merkle Trees:** Detect any transaction tampering efficiently
- **Difficulty Validation:** Blocks must meet minimum difficulty requirement

#### Layer 3: Network Security
- **Longest Chain Rule:** Nodes converge to the longest valid chain
- **Base Difficulty Sync:** Prevents difficulty divergence across nodes
- **Stake Persistence:** Reputation values survive restarts
- **Peer Heartbeat:** Stale peers automatically removed (30s timeout)

#### Layer 4: Consensus Security
- **Hybrid PoW+PoS:** Combines computational security with economic incentives
- **Stake Rewards:** Honest miners accumulate advantage over time
- **Fork Resolution:** Deterministic rule (longest chain) prevents splits
- **Chain Validation:** Full verification including Merkle roots on sync

## Advanced Features

### 1. Dynamic Difficulty Adjustment

**Purpose:** Maintain stable block production rate despite varying network hash power.

**Algorithm:**
```
Every DIFFICULTY_ADJUSTMENT_INTERVAL blocks (default: 3):
1. Calculate average time between recent blocks
2. Compare to target range (15-20 seconds)
3. If too fast (< 15s): base_difficulty += 1
4. If too slow (> 20s): base_difficulty -= 1
5. Constrain to [MIN_DIFFICULTY, MAX_DIFFICULTY]
```

**Benefits:**
- Adapts to network size (3 nodes vs 100 nodes)
- Prevents monopolization by high-power miners
- Maintains predictable block times

### 2. Hybrid PoW+PoS Consensus

**Why Hybrid?**
- **PoW provides security:** Expensive to create blocks
- **PoS provides efficiency:** Rewards honest participation
- **No token required:** Stake represents reputation, not currency

**Stake Mechanics:**
```
Initial state: All nodes have stake = 0 (equal opportunity)

Mining success: stake += 1 (reputation earned)

Mining advantage: difficulty -= (stake // 7)
  - Stake 7: -1 difficulty (2x easier)
  - Stake 14: -2 difficulty (4x easier)

Result: "Rich get richer" but:
  - New nodes can still participate (minimum difficulty)
  - Stake earned through work, not bought
  - Appropriate for reputation-based voting system
```

### 3. Digital Signatures (RSA-2048)

**Key Generation:**
```
Public/Private Keypair:
- Algorithm: RSA
- Key size: 2048 bits
- Padding: PSS (Probabilistic Signature Scheme)
- Hash: SHA-256

Voter ID:
- SHA-256 hash of public key
- First 16 characters used as unique identifier
```

**Signing Process:**
```
Message: "{voter_id}:{choice}:{timestamp}"
Signature: RSA_Sign(message, private_key)
Storage: Hex-encoded signature in transaction
```

**Security Properties:**
- **Unforgeable:** Cannot create valid signature without private key
- **Non-repudiation:** Signer cannot deny having signed
- **Integrity:** Any message modification invalidates signature
- **Public Verification:** Anyone can verify with public key

### 4. Merkle Tree Verification

**Purpose:** Efficiently prove transaction inclusion and detect tampering.

**Construction:**
```
Transactions: [Tx1, Tx2, Tx3, Tx4]

Level 0 (Leaves):
  H1 = hash(Tx1)
  H2 = hash(Tx2)
  H3 = hash(Tx3)
  H4 = hash(Tx4)

Level 1:
  H12 = hash(H1 + H2)
  H34 = hash(H3 + H4)

Level 2 (Root):
  Merkle_Root = hash(H12 + H34)
```

**Benefits:**
- **Tamper Detection:** Any transaction change → Different Merkle root → Invalid block
- **Efficient Verification:** Verify single transaction with log(N) hashes
- **Light Clients:** Can verify transactions without downloading full block

**Odd Number Handling:**
```
If 3 transactions:
  [H1, H2, H3] → [H1, H2, H3, H3]  (duplicate last)
  Then build tree normally
```

## UI Features

### Dashboard Tab
- **Node Status Cards:** ID, block count, stake, mining difficulty, peers
- **Stake Leaderboard:** All nodes ranked by reputation with mining advantages
- **Difficulty Monitor:** Real-time base and mining difficulty with adjustment status
- **Live Blockchain View:** Scrollable block cards showing:
  - Block hash and previous hash
  - Merkle root (purple)
  - Miner info (ID, stake, difficulties used)
  - Transaction list with signatures

### Vote Tab
- **Key Management:**
  - Generate RSA keypair with one click
  - View Voter ID and public key
  - Show/hide private key
  - Auto-delete after voting
- **Voting Form:**
  - Optional display name (human-readable)
  - Candidate selection (Alice, Bob, Charlie, Dave)
  - Cryptographic signing automatic
  - Success confirmation with auto-reset

### Mine Tab
- **Mining Advantage Panel:**
  - Your current stake
  - Base difficulty (network-wide)
  - Your mining difficulty (with stake bonus)
  - Stake bonus display
- **Mining Console:**
  - One-click mining button
  - Status feedback

### Results Tab
- **Visual vote tallying:**
  - Candidate names with vote counts
  - Percentage bars
  - Real-time updates

## Data Persistence

### Blockchain Data
- **Location:** `data/chain_<node_id>.json`
- **Contains:** Full chain with all blocks and transactions
- **Format:** JSON with nested objects
- **Persistence:** Saves after each mined block

### Stake Data
- **Location:** `data/stake_<node_id>.json`
- **Contains:** Current stake value and stake history
- **Persistence:** Saves after each successful mining
- **Recovery:** Automatically loaded on node restart

### Voting Keys
- **Location:** Browser localStorage
- **Contains:** Private key, public key, voter ID
- **Lifecycle:** Generated → Vote → Auto-deleted
- **Security:** Never transmitted to server, only signatures sent

## Technical Specifications

### Cryptography
- **Algorithm:** RSA with PSS padding
- **Key Size:** 2048 bits
- **Hash Function:** SHA-256
- **Signature Encoding:** Hexadecimal

### Proof-of-Work
- **Algorithm:** SHA-256 hash with leading zeros
- **Difficulty Range:** 1-5 leading zeros
- **Average Mining Time:** Varies by difficulty (1s to 30s)

### Merkle Tree
- **Hash Function:** SHA-256
- **Odd Nodes:** Duplicate last node
- **Empty Blocks:** Hash of empty byte string

## Security Considerations

### Why Security Features Matter

**Merkle Trees:**
- Detect tampering without checking every transaction
- Enable light clients (SPV)
- Used by Bitcoin, Ethereum

**Digital Signatures:**
- Prove vote authenticity
- Prevent impersonation
- Enable non-repudiation

**Hybrid Consensus:**
- PoW prevents rapid block creation
- PoS rewards long-term honest behavior
- Balances security and efficiency

## Quick Reference

### Key Commands
```bash
# Start everything
python run_network.py

# Clear all data and restart fresh
rm -rf data/*.json && python run_network.py

# Manual tracker start
uvicorn network.tracker:app --port 9000

# Manual node start
export NODE_ID=node-1 && export NODE_PORT=8000 && uvicorn api.server:app --port 8000
```

### Key URLs
- Node 1: http://localhost:8000
- Node 2: http://localhost:8001
- Node 3: http://localhost:8002
- Tracker: http://localhost:9000
- API Docs (any node): http://localhost:8000/docs

### Important Files
- `config.py` - Adjust all system parameters
- `core/node.py` line 58 - Modify stake bonus formula
- `data/stake_*.json` - Stake persistence (auto-generated)
- `data/chain_*.json` - Blockchain persistence (auto-generated)

### Stake Formula (Customizable)
```python
# In core/node.py line 58
stake_bonus = min(self.stake // 7, MAX_STAKE_INFLUENCE)
#                          ↑ Change this number to adjust stake sensitivity
```

**Examples:**
- `// 3` - Every 3 stake = -1 difficulty (fast rewards)
- `// 7` - Every 7 stake = -1 difficulty (current, balanced)
- `// 10` - Every 10 stake = -1 difficulty (slow rewards)

---
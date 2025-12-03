# core/blockchain.py
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from config import (
    BASE_DIFFICULTY,
    MIN_DIFFICULTY,
    MAX_DIFFICULTY,
    TARGET_BLOCK_TIME,
    DIFFICULTY_ADJUSTMENT_INTERVAL,
    DIFFICULTY_INCREASE_THRESHOLD,
    DIFFICULTY_DECREASE_THRESHOLD
)

@dataclass
class Transaction:
    """
    Represents a single vote in the system with digital signature support.
    """
    voter_id: str
    choice: str
    timestamp: float = field(default_factory=time.time)
    signature: str = ""
    public_key: str = ""
    username: str = ""  # Optional display name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voter_id": self.voter_id,
            "choice": self.choice,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "public_key": self.public_key,
            "username": self.username,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            voter_id=data["voter_id"],
            choice=data["choice"],
            timestamp=data.get("timestamp", time.time()),
            signature=data.get("signature", ""),
            public_key=data.get("public_key", ""),
            username=data.get("username", ""),
        )

    def compute_hash(self) -> str:
        tx_string = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()
    
    def get_message_for_signing(self) -> str:
        """
        Get the canonical message string that should be signed.
        Excludes signature field to avoid circular dependency.
        """
        return f"{self.voter_id}:{self.choice}:{self.timestamp}"
    
    def sign(self, private_key: str) -> None:
        """
        Sign this transaction with the given private key.
        
        Args:
            private_key: PEM-encoded RSA private key
        """
        from .crypto import sign_message
        message = self.get_message_for_signing()
        self.signature = sign_message(message, private_key)
    
    def verify(self) -> bool:
        """
        Verify that the signature is valid for this transaction.
        
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not self.signature or not self.public_key:
            # No signature to verify (legacy transaction or invalid)
            return False
        
        from .crypto import verify_signature
        message = self.get_message_for_signing()
        return verify_signature(message, self.signature, self.public_key)


@dataclass
class Block:
    """
    Proof-of-work block with stake-based difficulty adjustment.
    Combines PoW security with PoS-like incentives through reputation staking.
    Uses Merkle tree for efficient transaction integrity verification.
    """
    index: int
    transactions: List[Transaction]
    previous_hash: str
    timestamp: float = field(default_factory=time.time)
    nonce: int = 0
    hash: str = ""
    miner_id: str = ""  # ID of the node that mined this block
    stake: int = 0  # Miner's stake value at time of mining
    difficulty: int = 0  # Actual difficulty used to mine this block
    base_difficulty: int = 0  # Network base difficulty at time of mining
    merkle_root: str = ""  # Merkle root of all transactions in this block
    
    def __post_init__(self):
        """Calculate merkle root after initialization if not already set."""
        if not self.merkle_root:
            self.merkle_root = self._calculate_merkle_root()
    
    def _calculate_merkle_root(self) -> str:
        """
        Calculate the Merkle root of all transactions in this block.
        
        A Merkle tree is a binary tree where:
        - Leaves are hashes of individual transactions
        - Each parent node is the hash of its two children
        - The root represents a cryptographic commitment to all transactions
        
        Returns:
            str: Hex string of the Merkle root hash
        """
        if not self.transactions:
            # Empty block: return hash of empty string
            return hashlib.sha256(b"").hexdigest()
        
        # Get hash of each transaction
        hashes = [tx.compute_hash() for tx in self.transactions]
        
        # Build tree bottom-up until we have a single root
        while len(hashes) > 1:
            # If odd number of hashes, duplicate the last one
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            
            # Combine pairs of hashes
            new_level = []
            for i in range(0, len(hashes), 2):
                combined = f"{hashes[i]}{hashes[i+1]}"
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_level.append(parent_hash)
            
            hashes = new_level
        
        return hashes[0]

    def compute_hash(self) -> str:
        # note: we don't include self.hash in the data used to compute the hash
        block_data = {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "miner_id": self.miner_id,
            "stake": self.stake,
            "difficulty": self.difficulty,
            "base_difficulty": self.base_difficulty,
            "merkle_root": self.merkle_root,
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def verify_merkle_root(self) -> bool:
        """
        Verify that the merkle_root matches the transactions in this block.
        
        Returns:
            bool: True if merkle root is valid
        """
        expected_merkle = self._calculate_merkle_root()
        return self.merkle_root == expected_merkle
    
    def mine(self, difficulty: int = 2) -> None:
        """
        Simple proof-of-work: find a hash with `difficulty` leading zeros.
        Records the actual difficulty used for this block.
        Merkle root is calculated before mining and included in the block hash.
        """
        self.difficulty = difficulty  # Store the difficulty used
        
        # Ensure merkle root is calculated before mining
        if not self.merkle_root:
            self.merkle_root = self._calculate_merkle_root()
        
        target_prefix = "0" * difficulty
        # recompute hash each time nonce is updated
        self.hash = self.compute_hash()
        while not self.hash.startswith(target_prefix):
            self.nonce += 1
            self.hash = self.compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash,
            "miner_id": self.miner_id,
            "stake": self.stake,
            "difficulty": self.difficulty,
            "base_difficulty": self.base_difficulty,
            "merkle_root": self.merkle_root,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        txs = [Transaction.from_dict(tx) for tx in data.get("transactions", [])]
        
        # Get stored merkle_root if available, otherwise will be calculated in __post_init__
        stored_merkle = data.get("merkle_root", "")
        
        block = cls(
            index=data["index"],
            transactions=txs,
            previous_hash=data["previous_hash"],
            timestamp=data.get("timestamp", time.time()),
            nonce=data.get("nonce", 0),
            miner_id=data.get("miner_id", ""),
            stake=data.get("stake", 0),
            difficulty=data.get("difficulty", 0),
            base_difficulty=data.get("base_difficulty", 0),
            merkle_root=stored_merkle,
        )
        
        # If merkle_root was not stored, __post_init__ will calculate it
        # If a stored hash exists, keep it; otherwise compute one.
        stored_hash = data.get("hash")
        block.hash = stored_hash or block.compute_hash()
        return block


class Blockchain:
    """
    Minimal blockchain for a decentralized voting system.

    - Stores votes as transactions in blocks.
    - Uses proof-of-work mining with dynamic difficulty adjustment.
    - Enforces at-most-once voting by voter_id.
    """

    def __init__(self, base_difficulty: int = BASE_DIFFICULTY) -> None:
        self.base_difficulty = base_difficulty
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self._create_genesis_block()

    # core chain management

    def _create_genesis_block(self) -> None:
        genesis = Block(
            index=0,
            transactions=[],
            previous_hash="0",
            timestamp=0.0 # set to 0.0 for fixed timestamp
        )
        genesis.mine(self.base_difficulty)
        self.chain.append(genesis)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]
    
    def sync_base_difficulty_from_chain(self) -> None:
        """
        Sync base_difficulty from the latest block in the chain.
        This ensures all nodes converge to the same base_difficulty after syncing.
        """
        if len(self.chain) > 1:
            # Use the base_difficulty from the most recent block
            latest_base = self.last_block.base_difficulty
            if latest_base > 0:  # Only update if block has valid base_difficulty
                self.base_difficulty = latest_base

    # voting logic
    
    def has_voted(self, voter_id: str) -> bool:
        """
        Check if a voter_id already appears in the pending pool or confirmed chain.
        """
        # pending pool
        for tx in self.pending_transactions:
            if tx.voter_id == voter_id:
                return True

        # confirmed blocks
        for block in self.chain:
            for tx in block.transactions:
                if tx.voter_id == voter_id:
                    return True

        return False

    def cast_vote(self, voter_id: str, choice: str) -> bool:
        """
        Public API for casting a vote (legacy, no signature).

        Returns True if the vote was accepted,
        False if this voter has already voted.
        """
        if self.has_voted(voter_id):
            # voter already participated
            return False

        tx = Transaction(voter_id=voter_id, choice=choice)
        self.pending_transactions.append(tx)
        return True
    
    def cast_signed_vote(self, choice: str, private_key: str, public_key: str, username: str = "") -> tuple[bool, str]:
        """
        Cast a vote with digital signature authentication.
        
        Args:
            choice: The candidate to vote for
            private_key: PEM-encoded private key for signing
            public_key: PEM-encoded public key
            username: Optional display name for the voter
            
        Returns:
            tuple: (success: bool, error_message: str)
        """
        from .crypto import hash_public_key
        
        # Generate voter ID from public key
        voter_id = hash_public_key(public_key)
        
        # Check if already voted
        if self.has_voted(voter_id):
            return False, "duplicate_voter"
        
        # Create and sign transaction
        tx = Transaction(
            voter_id=voter_id,
            choice=choice,
            public_key=public_key,
            username=username
        )
        tx.sign(private_key)
        
        # Verify signature immediately
        if not tx.verify():
            return False, "invalid_signature"
        
        # Add to pending pool
        self.pending_transactions.append(tx)
        return True, ""

    def add_transaction(self, voter_id: str, choice: str) -> bool:
        return self.cast_vote(voter_id, choice)

    def calculate_average_block_time(self) -> float:
        """
        Calculate the average time between blocks in recent history.
        
        Caps individual block times at 5x the target to avoid long pauses
        skewing the average too much.
        
        Returns:
            float: Average block time in seconds, or TARGET_BLOCK_TIME if insufficient data
        """
        if len(self.chain) < 2:
            return TARGET_BLOCK_TIME
        
        # Get the most recent blocks for analysis
        num_blocks = min(DIFFICULTY_ADJUSTMENT_INTERVAL, len(self.chain))
        recent_blocks = self.chain[-num_blocks:]
        
        # Cap for individual block times to avoid extreme outliers
        MAX_BLOCK_TIME_CAP = TARGET_BLOCK_TIME * 5  # 50 seconds
        
        # Calculate time differences between consecutive blocks
        time_diffs = []
        for i in range(1, len(recent_blocks)):
            time_diff = recent_blocks[i].timestamp - recent_blocks[i-1].timestamp
            # Ignore genesis block with timestamp 0
            if recent_blocks[i-1].timestamp > 0 and time_diff > 0:
                # Cap extreme values to avoid long pauses affecting difficulty too much
                capped_diff = min(time_diff, MAX_BLOCK_TIME_CAP)
                time_diffs.append(capped_diff)
        
        if not time_diffs:
            return TARGET_BLOCK_TIME
        
        return sum(time_diffs) / len(time_diffs)
    
    def get_difficulty_adjustment_info(self) -> Dict[str, Any]:
        """
        Get detailed information about difficulty adjustment status.
        
        Returns:
            dict: Information about why difficulty is/isn't adjusting
        """
        avg_time = self.calculate_average_block_time()
        blocks_until_adjustment = max(0, DIFFICULTY_ADJUSTMENT_INTERVAL - len(self.chain))
        
        adjustment_reason = "stable"
        if len(self.chain) < DIFFICULTY_ADJUSTMENT_INTERVAL:
            adjustment_reason = "insufficient_blocks"
        elif avg_time < DIFFICULTY_INCREASE_THRESHOLD:
            adjustment_reason = "too_fast"
        elif avg_time > DIFFICULTY_DECREASE_THRESHOLD:
            adjustment_reason = "too_slow"
        
        return {
            "current_base_difficulty": self.base_difficulty,
            "avg_block_time": avg_time,
            "blocks_until_adjustment": blocks_until_adjustment,
            "adjustment_reason": adjustment_reason,
            "will_increase": avg_time < DIFFICULTY_INCREASE_THRESHOLD and len(self.chain) >= DIFFICULTY_ADJUSTMENT_INTERVAL,
            "will_decrease": avg_time > DIFFICULTY_DECREASE_THRESHOLD and len(self.chain) >= DIFFICULTY_ADJUSTMENT_INTERVAL,
        }
    
    def adjust_difficulty(self) -> int:
        """
        Dynamically adjust mining difficulty based on recent block times.
        
        If blocks are mined too quickly, increase difficulty.
        If blocks are mined too slowly, decrease difficulty.
        
        Returns:
            int: The adjusted difficulty value
        """
        # Only adjust after sufficient blocks have been mined
        if len(self.chain) < DIFFICULTY_ADJUSTMENT_INTERVAL:
            return self.base_difficulty
        
        avg_time = self.calculate_average_block_time()
        
        old_difficulty = self.base_difficulty
        
        # If average block time is too fast, increase difficulty
        if avg_time < DIFFICULTY_INCREASE_THRESHOLD:
            self.base_difficulty = min(MAX_DIFFICULTY, self.base_difficulty + 1)
            if self.base_difficulty > old_difficulty:
                print(f"[Blockchain] Difficulty increased: {old_difficulty} -> {self.base_difficulty} (avg time: {avg_time:.1f}s)")
        
        # If average block time is too slow, decrease difficulty
        elif avg_time > DIFFICULTY_DECREASE_THRESHOLD:
            self.base_difficulty = max(MIN_DIFFICULTY, self.base_difficulty - 1)
            if self.base_difficulty < old_difficulty:
                print(f"[Blockchain] Difficulty decreased: {old_difficulty} -> {self.base_difficulty} (avg time: {avg_time:.1f}s)")
        
        return self.base_difficulty

    def mine_pending_transactions(self, miner_id: str = "", stake: int = 0, 
                                   custom_difficulty: Optional[int] = None) -> Optional[Block]:
        """
        Package all pending transactions into a new block and mine it.
        Automatically adjusts difficulty based on recent block times and miner stake.
        
        Args:
            miner_id: ID of the miner mining this block
            stake: Miner's current stake value
            custom_difficulty: If provided, use this difficulty instead of auto-calculated
            
        Returns:
            Block or None: The mined block or None if there were no transactions.
        """
        if not self.pending_transactions:
            return None

        # Use custom difficulty if provided, otherwise adjust automatically
        if custom_difficulty is not None:
            current_difficulty = custom_difficulty
        else:
            current_difficulty = self.adjust_difficulty()

        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.last_block.hash,
            miner_id=miner_id,
            stake=stake,
            base_difficulty=self.base_difficulty,
        )
        new_block.mine(current_difficulty)
        self.chain.append(new_block)

        # Clear pending pool
        self.pending_transactions = []
        return new_block

    def is_chain_valid(self) -> bool:
        """
        Verify that:
        - the hash of each block is correct
        - the previous_hash links are consistent
        - each block satisfies minimum difficulty requirement
        - merkle root matches the transactions (if present)
        """
        if not self.chain:
            return True

        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Recompute hash and compare
            if current.hash != current.compute_hash():
                return False

            # Check link
            if current.previous_hash != previous.hash:
                return False

            # Check proof-of-work with minimum difficulty requirement
            if not current.hash.startswith("0" * MIN_DIFFICULTY):
                return False
            
            # Verify merkle root if present
            if current.merkle_root and not current.verify_merkle_root():
                return False

        return True

    def get_vote_results(self) -> Dict[str, int]:
        """
        Count votes per choice across the confirmed chain.
        """
        results: Dict[str, int] = {}
        for block in self.chain:
            for tx in block.transactions:
                results[tx.choice] = results.get(tx.choice, 0) + 1
        return results

    # simple console display helpers for debugging
    def display_chain(self) -> None:
        print("\n" + "=" * 60)
        print("Blockchain Status")
        print("=" * 60)

        for block in self.chain:
            print(f"\nBlock #{block.index}")
            ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp))
            print(f"  Timestamp: {ts_str}")
            print(f"  Previous Hash: {block.previous_hash[:16]}...")
            print(f"  Hash:          {block.hash[:16]}...")
            print(f"  Nonce:         {block.nonce}")
            print(f"  Transactions:  {len(block.transactions)}")
            for tx in block.transactions:
                print(
                    f"    - {tx.voter_id} -> {tx.choice} "
                    f"({time.strftime('%H:%M:%S', time.localtime(tx.timestamp))})"
                )

        print("\n" + "=" * 60 + "\n")

    def display_results(self) -> None:
        results = self.get_vote_results()

        print("\n" + "=" * 60)
        print("Voting Results")
        print("=" * 60)

        if not results:
            print("No votes yet.")
        else:
            total_votes = sum(results.values())
            print(f"Total votes: {total_votes}\n")

            for choice, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_votes) * 100 if total_votes else 0
                bar = "█" * int(percentage / 2)
                print(f"{choice:15} | {bar} {count} votes ({percentage:.1f}%)")

        print("=" * 60 + "\n")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_difficulty": self.base_difficulty,
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Blockchain":
        # Support both old 'difficulty' and new 'base_difficulty' keys for backward compatibility
        difficulty = data.get("base_difficulty", data.get("difficulty", BASE_DIFFICULTY))
        bc = cls(base_difficulty=difficulty)
        bc.chain = [Block.from_dict(b) for b in data.get("chain", [])]
        
        # if chain list was empty, ensure we have at least a genesis block
        if not bc.chain:
            bc._create_genesis_block()
        bc.pending_transactions = [
            Transaction.from_dict(t) for t in data.get("pending_transactions", [])
        ]
        return bc

    def save_to_file(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path: str) -> "Blockchain":
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            # new chain
            return cls()

        return cls.from_dict(data)

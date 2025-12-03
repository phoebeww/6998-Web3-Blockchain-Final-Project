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
    Represents a single vote in the system.
    """
    voter_id: str
    choice: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voter_id": self.voter_id,
            "choice": self.choice,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            voter_id=data["voter_id"],
            choice=data["choice"],
            timestamp=data.get("timestamp", time.time()),
        )

    def compute_hash(self) -> str:
        tx_string = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()


@dataclass
class Block:
    """
    Basic proof-of-work block for the voting chain.
    """
    index: int
    transactions: List[Transaction]
    previous_hash: str
    timestamp: float = field(default_factory=time.time)
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        # note: we don't include self.hash in the data used to compute the hash
        block_data = {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine(self, difficulty: int = 2) -> None:
        """
        Simple proof-of-work: find a hash with `difficulty` leading zeros.
        """
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
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        txs = [Transaction.from_dict(tx) for tx in data.get("transactions", [])]
        block = cls(
            index=data["index"],
            transactions=txs,
            previous_hash=data["previous_hash"],
            timestamp=data.get("timestamp", time.time()),
            nonce=data.get("nonce", 0),
        )
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
        Public API for casting a vote.

        Returns True if the vote was accepted,
        False if this voter has already voted.
        """
        if self.has_voted(voter_id):
            # voter already participated
            return False

        tx = Transaction(voter_id=voter_id, choice=choice)
        self.pending_transactions.append(tx)
        return True

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
        
        # If average block time is too fast, increase difficulty
        if avg_time < DIFFICULTY_INCREASE_THRESHOLD:
            self.base_difficulty = min(MAX_DIFFICULTY, self.base_difficulty + 1)
        
        # If average block time is too slow, decrease difficulty
        elif avg_time > DIFFICULTY_DECREASE_THRESHOLD:
            self.base_difficulty = max(MIN_DIFFICULTY, self.base_difficulty - 1)
        
        return self.base_difficulty

    def mine_pending_transactions(self) -> Optional[Block]:
        """
        Package all pending transactions into a new block and mine it.
        Automatically adjusts difficulty based on recent block times.
        Returns the mined block, or None if there were no transactions.
        """
        if not self.pending_transactions:
            return None

        # Adjust difficulty before mining
        current_difficulty = self.adjust_difficulty()

        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.last_block.hash,
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

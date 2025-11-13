import hashlib
import json
import time
from typing import List, Dict, Any

class Transaction:
    
    def __init__(self, voter_id: str, choice: str):
        self.voter_id = voter_id
        self.choice = choice
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'voter_id': self.voter_id,
            'choice': self.choice,
            'timestamp': self.timestamp
        }
    
    def compute_hash(self) -> str:
        tx_string = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()


class Block:
    """Block"""
    
    def __init__(self, index: int, transactions: List[Transaction], 
                 previous_hash: str, timestamp: float = None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp else time.time()
        self.nonce = 0
        self.hash = self.compute_hash()
    
    def compute_hash(self) -> str:
        block_data = {
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'nonce': self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty: int = 2):
        target = '0' * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()
        print(f"Block mined! Nonce: {self.nonce}, Hash: {self.hash[:16]}...")


class Blockchain:
    """Blockchain"""
    
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = 2
        self.create_genesis_block()
    
    def create_genesis_block(self):
        genesis_block = Block(0, [], "0")
        self.chain.append(genesis_block)
    
    def get_last_block(self) -> Block:
        return self.chain[-1]
    
    def add_transaction(self, voter_id: str, choice: str) -> bool:
        # Check if voter has already voted
        if self.has_voted(voter_id):
            print(f"Error: Voter {voter_id} has already voted!")
            return False
        
        transaction = Transaction(voter_id, choice)
        self.pending_transactions.append(transaction)
        print(f"Vote added: {voter_id} -> {choice}")
        return True
    
    def has_voted(self, voter_id: str) -> bool:
        # Check pending transactions
        for tx in self.pending_transactions:
            if tx.voter_id == voter_id:
                return True
        
        # Check confirmed transactions in the chain
        for block in self.chain:
            for tx in block.transactions:
                if tx.voter_id == voter_id:
                    return True
        
        return False
    
    def mine_pending_transactions(self):
        if not self.pending_transactions:
            print("No pending transactions")
            return False
        
        print(f"\nStarting mining... (Difficulty: {self.difficulty})")
        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions,
            previous_hash=self.get_last_block().hash
        )
        
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.pending_transactions = []
        
        print(f"New block added to the chain! Block #{new_block.index}\n")
        return True
    
    def is_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Validate current block hash
            if current_block.hash != current_block.compute_hash():
                print(f"Invalid hash at block {i}")
                return False
            
            # Validate link
            if current_block.previous_hash != previous_block.hash:
                print(f"Invalid link at block {i}")
                return False
            
            # Validate proof of work
            if not current_block.hash.startswith('0' * self.difficulty):
                print(f"Invalid proof of work at block {i}")
                return False
        
        return True
    
    def get_vote_results(self) -> Dict[str, int]:
        results = {}
        
        for block in self.chain:
            for tx in block.transactions:
                choice = tx.choice
                results[choice] = results.get(choice, 0) + 1
        
        return results
    
    def display_chain(self):
        print("\n" + "="*60)
        print("Blockchain Status")
        print("="*60)
        
        for block in self.chain:
            print(f"\nBlock #{block.index}")
            print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}")
            print(f"  Previous Hash: {block.previous_hash[:16]}...")
            print(f"  Current Hash: {block.hash[:16]}...")
            print(f"  Nonce: {block.nonce}")
            print(f"  Transaction Count: {len(block.transactions)}")
            
            if block.transactions:
                print("  Transactions:")
                for tx in block.transactions:
                    print(f"    - {tx.voter_id} voted for {tx.choice}")
        
        print("\n" + "="*60)
    
    def display_results(self):
        results = self.get_vote_results()
        
        print("\n" + "="*60)
        print("Voting Results")
        print("="*60)
        
        if not results:
            print("No votes yet")
        else:
            total_votes = sum(results.values())
            print(f"Total votes: {total_votes}\n")
            
            for choice, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_votes) * 100
                bar = "█" * int(percentage / 2)
                print(f"{choice:15} | {bar} {count} votes ({percentage:.1f}%)")
        
        print("="*60 + "\n")

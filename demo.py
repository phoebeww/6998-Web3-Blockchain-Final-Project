#!/usr/bin/env python3
"""
Quick Demo Script - Show basic functionality of the Voting System
"""

from mvp_blockchain import Blockchain

def demo():
    print("\n" + "="*60)
    print("Distributed Voting System MVP - Automatic Demo")
    print("="*60)
    
    # Create blockchain
    print("\n1. Creating blockchain...")
    blockchain = Blockchain()
    print("✓ Blockchain created (includes genesis block)")
    
    # Add votes
    print("\n2. Adding votes...")
    votes = [
        ("alice", "Candidate A"),
        ("bob", "Candidate B"),
        ("charlie", "Candidate A"),
        ("david", "Candidate C"),
        ("eve", "Candidate A"),
    ]
    
    for voter_id, choice in votes:
        blockchain.add_transaction(voter_id, choice)
    
    print(f"✓ Added {len(votes)} votes to the pending transaction pool")
    
    # Attempt duplicate vote
    print("\n3. Testing duplicate vote prevention...")
    blockchain.add_transaction("alice", "Candidate B")  # Should fail
    
    # Mining
    print("\n4. Mining (packaging transactions into a block)...")
    blockchain.mine_pending_transactions()
    
    # Display blockchain
    blockchain.display_chain()
    
    # Display voting results
    blockchain.display_results()
    
    # Validate blockchain
    print("\n5. Verifying blockchain integrity...")
    is_valid = blockchain.is_valid()
    if is_valid:
        print("✓ Blockchain verification passed!")
    else:
        print("✗ Blockchain verification failed!")
    
    # Add more votes
    print("\n6. Adding second batch of votes...")
    more_votes = [
        ("frank", "Candidate B"),
        ("grace", "Candidate A"),
        ("henry", "Candidate C"),
    ]
    
    for voter_id, choice in more_votes:
        blockchain.add_transaction(voter_id, choice)
    
    print(f"✓ Added {len(more_votes)} new votes")
    
    # Mine again
    print("\n7. Mining second block...")
    blockchain.mine_pending_transactions()
    
    # Final results
    blockchain.display_chain()
    blockchain.display_results()
    
    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60)
    print("\nTip: Run 'python mvp_voting.py' to use the system interactively\n")

if __name__ == "__main__":
    demo()

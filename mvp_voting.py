#!/usr/bin/env python3
"""
Distributed Voting System
"""

from mvp_blockchain import Blockchain
import sys

def print_menu():
    print("\n" + "="*60)
    print("Distributed Voting System")
    print("="*60)
    print("1. Vote")
    print("2. Mine (package transactions)")
    print("3. View Blockchain")
    print("4. View Voting Results")
    print("5. Verify Blockchain")
    print("6. Exit")
    print("="*60)

def main():
    # Create blockchain
    blockchain = Blockchain()
    
    print("\nWelcome to the Distributed Voting System!")
    print("This is a simplified blockchain-based voting system.")
    
    while True:
        print_menu()
        choice = input("\nPlease select an option (1-6): ").strip()
        
        if choice == '1':
            # Voting
            print("\n--- Voting ---")
            voter_id = input("Enter your voter ID (e.g., voter1): ").strip()
            
            if not voter_id:
                print("Voter ID cannot be empty!")
                continue
            
            print("\nCandidates:")
            print("  A. Candidate A")
            print("  B. Candidate B")
            print("  C. Candidate C")
            
            vote_choice = input("\nSelect your candidate (A/B/C): ").strip().upper()
            
            if vote_choice not in ['A', 'B', 'C']:
                print("Invalid selection!")
                continue
            
            candidate_map = {'A': 'Candidate A', 'B': 'Candidate B', 'C': 'Candidate C'}
            candidate = candidate_map[vote_choice]
            
            success = blockchain.add_transaction(voter_id, candidate)
            
            if success:
                print(f"\n✓ Vote successful! Your vote has been added to the pending transaction pool.")
                print(f"  Note: Mining is required to record your vote on the blockchain.")
        
        elif choice == '2':
            # Mining
            print("\n--- Mining ---")
            
            if not blockchain.pending_transactions:
                print("No pending transactions, mining not needed.")
                continue
            
            print(f"Number of pending transactions: {len(blockchain.pending_transactions)}")
            confirm = input("Confirm start mining? (y/n): ").strip().lower()
            
            if confirm == 'y':
                blockchain.mine_pending_transactions()
        
        elif choice == '3':
            # View blockchain
            blockchain.display_chain()
        
        elif choice == '4':
            # View voting results
            blockchain.display_results()
        
        elif choice == '5':
            # Verify blockchain
            print("\n--- Verifying Blockchain ---")
            is_valid = blockchain.is_valid()
            
            if is_valid:
                print("✓ Blockchain verification passed! All blocks are valid.")
            else:
                print("✗ Blockchain verification failed! Tampering detected.")
        
        elif choice == '6':
            # Exit
            print("\nThank you for using the Distributed Voting System!")
            sys.exit(0)
        
        else:
            print("\nInvalid selection, please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram exited.")
        sys.exit(0)

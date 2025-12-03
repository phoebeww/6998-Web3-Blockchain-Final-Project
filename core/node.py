# core/node.py
from __future__ import annotations

import os
from typing import Dict, Any, List, Optional
import requests

from .blockchain import Blockchain, Block
from config import MIN_DIFFICULTY, BASE_DIFFICULTY


class Node:
    """
    A single blockchain node in the voting network.

    """

    def __init__(
        self,
        node_id: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        data_dir: str = "data",
        difficulty: int = BASE_DIFFICULTY,
    ) -> None:
        self.node_id = node_id
        self.host = host
        self.port = port
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        self.chain_path = os.path.join(self.data_dir, f"chain_{self.node_id}.json")

        self.blockchain: Blockchain = Blockchain.load_from_file(self.chain_path)
        self.blockchain.base_difficulty = difficulty

        # simple list of peers
        # e.g. [{"node_id": "node-2", "host": "127.0.0.1", "port": 8001}, ...]
        self.peers: List[Dict[str, Any]] = []


    def save_chain(self) -> None:
        self.blockchain.save_to_file(self.chain_path)

    def cast_vote(self, voter_id: str, choice: str) -> bool:
        """
        Try to cast a vote on this node.

        Returns:
            True  - vote accepted
            False - voter has already voted
        """
        accepted = self.blockchain.cast_vote(voter_id, choice)
        if accepted:
            # For now, we only persist on mining to reduce writes.
            # You could also persist here if you want stronger durability.
            pass
        return accepted

    def mine(self) -> Optional[Block]:
        """
        Mine a new block from pending transactions.
        Returns the new Block, or None if there is nothing to mine.
        """
        block = self.blockchain.mine_pending_transactions()
        if block is not None:
            self.save_chain()
            # broadcast the new block to peers!
            print(f"[{self.node_id}] Block mined. Broadcasting...")
            self.broadcast_block(block)
        return block

    def get_results(self) -> Dict[str, Any]:
        """
        Aggregate vote results from this node's chain.
        """
        results = self.blockchain.get_vote_results()
        total_votes = sum(results.values())
        return {
            "total_votes": total_votes,
            "results": [
                {
                    "choice": choice,
                    "count": count,
                    "percentage": (count / total_votes) * 100 if total_votes else 0.0,
                }
                for choice, count in sorted(results.items(), key=lambda x: x[1], reverse=True)
            ],
        }

    def get_chain_view(self) -> List[Dict[str, Any]]:
        """
        Return a JSON-serializable view of the chain.
        """
        return [block.to_dict() for block in self.blockchain.chain]

    def get_stats(self) -> Dict[str, Any]:
        """
        Basic stats useful for UI/status displays.
        Includes dynamic difficulty information.
        """
        results = self.blockchain.get_vote_results()
        total_votes = sum(results.values())

        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "blocks": len(self.blockchain.chain),
            "base_difficulty": self.blockchain.base_difficulty,
            "avg_block_time": self.blockchain.calculate_average_block_time(),
            "total_votes": total_votes,
            "chain_valid": self.blockchain.is_chain_valid(),
            "peers": len(self.peers),
        }

    # networking hooks
    
    def register_with_tracker(self, tracker_url: str) -> bool:
        print(f"[{self.node_id}] Registering with tracker at {tracker_url}...")
        payload = {"node_id": self.node_id, "host": self.host, "port": self.port}
        try:
            resp = requests.post(f"{tracker_url}/register", json=payload, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            # Store peers, exclude ourselves
            self.peers = [p for p in data.get("peers", []) if p["node_id"] != self.node_id]
            print(f"[{self.node_id}] Registered. Known peers: {len(self.peers)}")
            return True
        except Exception as e:
            print(f"[{self.node_id}] Failed to register with tracker: {e}")
            return False
            
    def sync_with_network(self) -> None:
        """
        find a peer and download their chain through http.
        """
        if not self.peers:
            return

        # <--- CHANGED: Loop through all peers until one works, instead of just peers[0]
        for peer in self.peers:
            target_node_id = peer['node_id']
            print(f"[{self.node_id}] Attempting sync from {target_node_id}...")
            
            try:
                # Direct Download from the peer's /chain endpoint
                url = f"http://{peer['host']}:{peer['port']}/chain"
                resp = requests.get(url, timeout=5)
                
                if resp.status_code == 200:
                    remote_chain_list = resp.json()
                    
                    # We need to wrap the list in a dict to match what Blockchain.from_dict expects
                    data_wrapper = {
                        "base_difficulty": self.blockchain.base_difficulty,
                        "chain": remote_chain_list,
                        "pending_transactions": []
                    }
                    
                    new_chain = Blockchain.from_dict(data_wrapper)
                    
                    # If valid and longer, replace ours
                    if new_chain.is_chain_valid() and len(new_chain.chain) > len(self.blockchain.chain):
                        self.blockchain = new_chain
                        self.save_chain()
                        print(f"[{self.node_id}] Sync successful from {target_node_id}. Current height: {len(self.blockchain.chain)}")
                        break # <--- ADDED: Stop looking if we successfully synced
                    else:
                        print(f"[{self.node_id}] Remote chain from {target_node_id} was not better. Sync skipped.")
            except Exception as e:
                print(f"[{self.node_id}] Sync failed from {target_node_id}: {e}")
                # Continue to next peer if this one failed
            
    def broadcast_block(self, block: Block) -> None:
        """Send the newly mined block to all known peers."""
        msg_payload = {
            "type": "NEW_BLOCK",
            "data": block.to_dict(),
            "sender_id": self.node_id
        }
        for peer in self.peers:
            url = f"http://{peer['host']}:{peer['port']}/message"
            try:
                requests.post(url, json=msg_payload, timeout=2)
            except Exception as e:
                print(f"[{self.node_id}] Failed to broadcast to {peer['node_id']}: {e}")

    def handle_incoming_message(self, message: Dict[str, Any]) -> None:
        msg_type = message.get("type")
        sender_id = message.get("sender_id")
        data = message.get("data", {})

        print(f"[{self.node_id}] Received {msg_type} from {sender_id}")

        if msg_type == "NEW_BLOCK":
            # 1. Parse block
            incoming_block = Block.from_dict(data)
            last_block = self.blockchain.last_block

            # 2. Check index
            if incoming_block.index == last_block.index + 1:
                # It fits perfectly. Verify hash linkage & validity
                if incoming_block.previous_hash == last_block.hash:
                    # Append logic is effectively "mining" but we verify PoW matches minimum difficulty
                    if incoming_block.hash.startswith("0" * MIN_DIFFICULTY):
                        self.blockchain.chain.append(incoming_block)
                        self.save_chain()
                        print(f"[{self.node_id}] Added Block #{incoming_block.index} from peer.")
                        # Remove any pending transactions that are now in this block
                        # (Simple implementation: just clear pending for now, or filter them)
                        self.blockchain.pending_transactions = []
                    else:
                        print(f"[{self.node_id}] Block rejected: Invalid PoW")
                else:
                    print(f"[{self.node_id}] Block rejected: Hash mismatch")
            elif incoming_block.index > last_block.index + 1:
                # We are behind. Request full chain.
                # Find the peer info to reply to
                print(f"[{self.node_id}] Gap detected. Re-syncing...")
                self.sync_with_network()

        elif msg_type == "REQUEST_CHAIN":
            # Send our chain back to the requester
            peer_info = next((p for p in self.peers if p["node_id"] == sender_id), None)
            if peer_info:
                url = f"http://{peer_info['host']}:{peer_info['port']}/message"
                resp_payload = {
                    "type": "CHAIN_RESPONSE",
                    "data": self.blockchain.to_dict(), # Sends full chain
                    "sender_id": self.node_id
                }
                try:
                    requests.post(url, json=resp_payload, timeout=5)
                except Exception:
                    pass

        elif msg_type == "CHAIN_RESPONSE":
            # Consensus: Longest Valid Chain Wins
            try:
                # Load potential new chain (data is a dict representation of Blockchain)
                incoming_chain_obj = Blockchain.from_dict(data)
                
                # Rule 1: Must be longer
                if len(incoming_chain_obj.chain) > len(self.blockchain.chain):
                    # Rule 2: Must be valid
                    if incoming_chain_obj.is_chain_valid():
                        print(f"[{self.node_id}] Replacing local chain (len {len(self.blockchain.chain)}) with new chain (len {len(incoming_chain_obj.chain)})")
                        self.blockchain = incoming_chain_obj
                        self.save_chain()
                    else:
                        print(f"[{self.node_id}] Received longer chain but it was invalid.")
                else:
                    print(f"[{self.node_id}] Received chain is not longer. Ignoring.")
            except Exception as e:
                print(f"[{self.node_id}] Error processing chain response: {e}")
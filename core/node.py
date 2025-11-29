# core/node.py
from __future__ import annotations

import os
from typing import Dict, Any, List, Optional
import requests

from .blockchain import Blockchain, Block


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
        difficulty: int = 2,
    ) -> None:
        self.node_id = node_id
        self.host = host
        self.port = port
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        self.chain_path = os.path.join(self.data_dir, f"chain_{self.node_id}.json")

        self.blockchain: Blockchain = Blockchain.load_from_file(self.chain_path)
        self.blockchain.difficulty = difficulty

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
        """
        results = self.blockchain.get_vote_results()
        total_votes = sum(results.values())

        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "blocks": len(self.blockchain.chain),
            "difficulty": self.blockchain.difficulty,
            "total_votes": total_votes,
            "chain_valid": self.blockchain.is_chain_valid(),
        }

    # networking hooks
    
    def register_with_tracker(self, tracker_url: str) -> None:
        """
        Call this once when the node starts.

        Example:
            node.register_with_tracker("http://127.0.0.1:9000")
        """
        payload = {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
        }

        resp = requests.post(f"{tracker_url}/register", json=payload, timeout=5)
        resp.raise_for_status()

        data = resp.json()
        reg = RegisterResponse(**data)

        # store peers, exclude ourselves (optional)
        self.peers = [
            p.dict()
            for p in reg.peers
            if p.node_id != self.node_id
        ]

    def update_peers(self, peers: List[Dict[str, Any]]) -> None:
        """
        Replace the current peer list with a new one.
        """
        self.peers = peers

    def broadcast_block(self, block: Block) -> None:
        """
        TODO:
        Send the newly mined block to all known peers.

        Suggested approach:
        - For each peer in self.peers:
            - POST to f"http://{peer['host']}:{peer['port']}/message"
            - with a Message(type="NEW_BLOCK", data=block.to_dict(), sender_id=self.node_id)
        """
        raise NotImplementedError("broadcast_block is not implemented yet")

    def request_chain_from_peer(self, peer: Dict[str, Any]) -> None:
        """
        TODO :
        Ask a specific peer for their full chain.

        Suggested approach:
        - POST a Message(type="REQUEST_CHAIN", data={}, sender_id=self.node_id)
          to that peer's /message endpoint.
        """
        raise NotImplementedError("request_chain_from_peer is not implemented yet")

    def handle_incoming_message(self, message: Dict[str, Any]) -> None:
        """
        TODO:
        Handle messages such as NEW_BLOCK, REQUEST_CHAIN, CHAIN_RESPONSE.

        Basic idea:
        - msg = Message(**message)
        - if msg.type == "NEW_BLOCK":
              -> validate block, try to append
              -> if block doesn't fit, maybe trigger REQUEST_CHAIN
        - elif msg.type == "REQUEST_CHAIN":
              -> send CHAIN_RESPONSE back to sender with our full chain
        - elif msg.type == "CHAIN_RESPONSE":
              -> rebuild a Blockchain from msg.data["chain"]
                 and adopt it if it's valid and better (longer).
        """
        raise NotImplementedError("handle_incoming_message is not implemented yet")
# network/tracker.py
from __future__ import annotations
import time
from typing import List, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel
from network.schemas import NodeInfo, RegisterRequest, RegisterResponse
from config import DEFAULT_STAKE, STAKE_REWARD, STAKE_PENALTY

app = FastAPI(title="Tracker Service")

# In-memory list of registered nodes

nodes: List[NodeInfo] = []
PEER_TIMEOUT = 20 

registered_nodes: Dict[str, Any] = {}

# Stake management for PoW + PoS hybrid consensus
node_stakes: Dict[str, int] = {}  # {node_id: stake_value}

def cleanup_stale_nodes():
    """
    Iterate through nodes and remove anyone who hasn't updated recently.
    """
    now = time.time()
    # Find IDs to remove
    dead_ids = []
    for node_id, data in registered_nodes.items():
        if now - data["last_seen"] > PEER_TIMEOUT:
            dead_ids.append(node_id)
    
    # Remove them
    for dead_id in dead_ids:
        print(f"[Tracker] Removing stale node: {dead_id}")
        del registered_nodes[dead_id]

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "registered_nodes": len(nodes)}


@app.post("/register", response_model=RegisterResponse)
def register(req: RegisterRequest) -> RegisterResponse:
    """
    A node calls this endpoint to register itself.

    - If it's new, we add it to the list.
    - If it already exists, we update its host/port (in case it restarted).
    - We return the full peer list so the node can store it in its self.peers.
    """
    global nodes

    node_info = NodeInfo(node_id=req.node_id, host=req.host, port=req.port)
    registered_nodes[req.node_id] = {
        "info": node_info,
        "last_seen": time.time()
    }

    cleanup_stale_nodes()

    active_peers = [data["info"] for data in registered_nodes.values()]
    return RegisterResponse(peers=active_peers)


@app.get("/peers", response_model=list[NodeInfo])
def get_peers() -> list[NodeInfo]:
    """
    Optional: useful for debugging or monitoring.
    """
    cleanup_stale_nodes()
    return [data["info"] for data in registered_nodes.values()]


class StakeUpdate(BaseModel):
    node_id: str
    stake: int


@app.post("/update_stake")
def update_stake(req: StakeUpdate) -> Dict[str, Any]:
    """
    Node reports its current stake value to the tracker.
    """
    node_stakes[req.node_id] = req.stake
    return {"ok": True, "stake": req.stake}


@app.get("/stakes")
def get_stakes() -> Dict[str, Any]:
    """
    Get the stake leaderboard of all nodes.
    Returns nodes sorted by stake in descending order.
    """
    cleanup_stale_nodes()
    
    # Build leaderboard with node info and stakes
    leaderboard = []
    for node_id, data in registered_nodes.items():
        info = data["info"]
        stake = node_stakes.get(node_id, DEFAULT_STAKE)
        leaderboard.append({
            "node_id": node_id,
            "host": info.host,
            "port": info.port,
            "stake": stake
        })
    
    # Sort by stake descending
    leaderboard.sort(key=lambda x: x["stake"], reverse=True)
    
    return {
        "leaderboard": leaderboard,
        "total_nodes": len(leaderboard)
    }


@app.get("/stake/{node_id}")
def get_node_stake(node_id: str) -> Dict[str, Any]:
    """
    Get the stake value for a specific node.
    """
    stake = node_stakes.get(node_id, DEFAULT_STAKE)
    return {"node_id": node_id, "stake": stake}

# network/tracker.py
from __future__ import annotations
import time
from typing import List, Dict, Any

from fastapi import FastAPI
from network.schemas import NodeInfo, RegisterRequest, RegisterResponse

app = FastAPI(title="Tracker Service")

# In-memory list of registered nodes

nodes: List[NodeInfo] = []
PEER_TIMEOUT = 20 

registered_nodes: Dict[str, Any] = {}

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

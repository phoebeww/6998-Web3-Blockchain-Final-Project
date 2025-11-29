# network/tracker.py
from __future__ import annotations

from typing import List

from fastapi import FastAPI
from network.schemas import NodeInfo, RegisterRequest, RegisterResponse

app = FastAPI(title="Tracker Service")

# In-memory list of registered nodes

nodes: List[NodeInfo] = []


def _find_node(node_id: str) -> int:
    for i, n in enumerate(nodes):
        if n.node_id == node_id:
            return i
    return -1


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
    idx = _find_node(req.node_id)

    if idx == -1:
        nodes.append(node_info)
    else:
        nodes[idx] = node_info

    # Return all peers (including the caller)
    return RegisterResponse(peers=nodes)


@app.get("/peers", response_model=list[NodeInfo])
def get_peers() -> list[NodeInfo]:
    """
    Optional: useful for debugging or monitoring.
    """
    return nodes

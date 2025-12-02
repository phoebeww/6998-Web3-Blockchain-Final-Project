# api/server.py
from __future__ import annotations
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List

from fastapi import FastAPI
from pydantic import BaseModel
from network.schemas import Message
from core.node import Node
from fastapi.middleware.cors import CORSMiddleware

# Read from environment or arguments to allow running multiple nodes
NODE_ID = os.getenv("NODE_ID", "node-1")
HOST = os.getenv("NODE_HOST", "127.0.0.1")
PORT = int(os.getenv("NODE_PORT", "8000"))
TRACKER_URL = os.getenv("TRACKER_URL", "http://127.0.0.1:9000")

async def periodic_peer_refresh(interval: int = 30):
    """
    Runs in the background. Every 'interval' seconds, it asks the tracker
    for the latest list of peers.
    """
    while True:
        # Wait first (so we don't double-register immediately on startup)
        await asyncio.sleep(interval)
        try:
            # This triggers the existing logic in core/node.py
            # You will see logs like "[node-1] Registering with tracker..." every 10s
            node.register_with_tracker(TRACKER_URL)
        except Exception as e:
            print(f"[{NODE_ID}] Auto-refresh failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # register
    print(f"[{NODE_ID}] Startup: Initial registration...")
    node.register_with_tracker(TRACKER_URL)
    
    # start the loop
    refresh_task = asyncio.create_task(periodic_peer_refresh(30))
    
    yield
    
    # cancel loop
    refresh_task.cancel()
    print(f"[{NODE_ID}] Shutting down.")

# app

app = FastAPI(title=f"Voting Node {NODE_ID}", lifespan=lifespan)
node = Node(node_id=NODE_ID, host=HOST, port=PORT)

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# models

class VoteRequest(BaseModel):
    voter_id: str
    choice: str


class VoteResponse(BaseModel):
    ok: bool
    error: Optional[str] = None


class MineResponse(BaseModel):
    mined: bool
    block: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class ResultsResponse(BaseModel):
    total_votes: int
    results: List[Dict[str, Any]]


class StatsResponse(BaseModel):
    node_id: str
    host: str
    port: int
    blocks: int
    difficulty: int
    total_votes: int
    chain_valid: bool
    peers: int


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "node_id": node.node_id}


@app.post("/vote", response_model=VoteResponse)
def cast_vote(req: VoteRequest) -> VoteResponse:
    accepted = node.cast_vote(req.voter_id, req.choice)
    if not accepted:
        return VoteResponse(ok=False, error="duplicate_voter")
    return VoteResponse(ok=True)


@app.post("/mine", response_model=MineResponse)
def mine_block() -> MineResponse:
    block = node.mine()
    if block is None:
        return MineResponse(mined=False, block=None, message="No pending transactions to mine.")
    return MineResponse(mined=True, block=block.to_dict(), message="Block mined successfully.")


@app.get("/results", response_model=ResultsResponse)
def get_results() -> ResultsResponse:
    data = node.get_results()
    return ResultsResponse(
        total_votes=data["total_votes"],
        results=data["results"],
    )


@app.get("/chain")
def get_chain() -> List[Dict[str, Any]]:
    return node.get_chain_view()


@app.get("/stats", response_model=StatsResponse)
def get_stats() -> StatsResponse:
    stats = node.get_stats()
    return StatsResponse(**stats)


@app.get("/validate")
def validate_chain() -> Dict[str, Any]:
    """
    check if the chain is currently valid.
    """
    valid = node.blockchain.is_chain_valid()
    return {"valid": valid}


@app.post("/message")
def receive_message(msg: Message) -> Dict[str, Any]:
    """
    Endpoint for other nodes to send P2P messages to this node.
    The heavy lifting is done inside node.handle_incoming_message.
    """
    node.handle_incoming_message(msg.model_dump())
    return {"ok": True}


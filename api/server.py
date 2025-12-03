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
from fastapi.staticfiles import StaticFiles

# Read from environment or arguments to allow running multiple nodes
NODE_ID = os.getenv("NODE_ID", "node-1")
HOST = os.getenv("NODE_HOST", "127.0.0.1")
PORT = int(os.getenv("NODE_PORT", "8000"))
TRACKER_URL = os.getenv("TRACKER_URL", "http://127.0.0.1:9000")

async def periodic_peer_refresh(interval: int = 10):
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
    success = False
    try:
        success = node.register_with_tracker(TRACKER_URL)
    except Exception as e:
        print(f"[{NODE_ID}] Startup warning: Tracker might be down ({e})")
    
    # sync
    if success and node.peers:
        node.sync_with_network()

    # background loop
    refresh_task = asyncio.create_task(periodic_peer_refresh(10))
    
    yield
    
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


class SignedVoteRequest(BaseModel):
    choice: str
    private_key: str
    public_key: str
    username: Optional[str] = ""


class VoteResponse(BaseModel):
    ok: bool
    error: Optional[str] = None
    voter_id: Optional[str] = None


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
    base_difficulty: int
    mining_difficulty: int
    stake: int
    stake_bonus: int
    avg_block_time: float
    total_votes: int
    chain_valid: bool
    peers: int
    difficulty_info: Dict[str, Any]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "node_id": node.node_id}


@app.get("/generate_keys")
def generate_keys() -> Dict[str, str]:
    """
    Generate a new RSA keypair for voting.
    """
    from core.crypto import generate_keypair, hash_public_key
    private_key, public_key = generate_keypair()
    voter_id = hash_public_key(public_key)
    
    return {
        "private_key": private_key,
        "public_key": public_key,
        "voter_id": voter_id
    }


@app.get("/config")
def get_config() -> Dict[str, Any]:
    """
    Get system configuration parameters for UI display.
    """
    from config import (
        TARGET_BLOCK_TIME,
        DIFFICULTY_INCREASE_THRESHOLD,
        DIFFICULTY_DECREASE_THRESHOLD,
        MAX_STAKE_INFLUENCE
    )
    
    return {
        "target_block_time": TARGET_BLOCK_TIME,
        "difficulty_increase_threshold": DIFFICULTY_INCREASE_THRESHOLD,
        "difficulty_decrease_threshold": DIFFICULTY_DECREASE_THRESHOLD,
        "max_stake_influence": MAX_STAKE_INFLUENCE
    }


@app.post("/vote", response_model=VoteResponse)
def cast_vote(req: VoteRequest) -> VoteResponse:
    accepted = node.cast_vote(req.voter_id, req.choice)
    if not accepted:
        return VoteResponse(ok=False, error="duplicate_voter")
    return VoteResponse(ok=True)


@app.post("/vote_signed", response_model=VoteResponse)
def cast_signed_vote(req: SignedVoteRequest) -> VoteResponse:
    """
    Cast a vote with digital signature authentication.
    """
    success, error = node.blockchain.cast_signed_vote(
        choice=req.choice,
        private_key=req.private_key,
        public_key=req.public_key,
        username=req.username or ""
    )
    
    if not success:
        return VoteResponse(ok=False, error=error)
    
    # Return voter ID for display
    from core.crypto import hash_public_key
    voter_id = hash_public_key(req.public_key)
    return VoteResponse(ok=True, voter_id=voter_id)


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


@app.get("/stakes")
def get_stake_leaderboard() -> Dict[str, Any]:
    """
    Get the stake leaderboard from the tracker.
    """
    try:
        resp = requests.get(f"{TRACKER_URL}/stakes", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Mark which node is the current one
            for node_data in data.get("leaderboard", []):
                node_data["is_current"] = node_data["node_id"] == node.node_id
            return data
        return {"leaderboard": [], "total_nodes": 0}
    except Exception:
        return {"leaderboard": [], "total_nodes": 0}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

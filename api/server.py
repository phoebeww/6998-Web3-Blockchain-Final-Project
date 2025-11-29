# api/server.py
from __future__ import annotations

from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from network.schemas import Message

from core.node import Node

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

# apps

app = FastAPI(title="Decentralized Voting Node API")

# For now we run a single node in this process.
# Later we can run multiple processes with different node_ids/ports.
# TODO - to be changed
node = Node(node_id="node-1", host="127.0.0.1", port=8000)


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


# network/schemas.py
from __future__ import annotations

from typing import Dict, Any, Optional
from pydantic import BaseModel


class NodeInfo(BaseModel):
    node_id: str
    host: str
    port: int


class RegisterRequest(BaseModel):
    node_id: str
    host: str
    port: int


class RegisterResponse(BaseModel):
    # full list of known peers
    peers: list[NodeInfo]


class Message(BaseModel):
    """
    Generic P2P message model between nodes.

    type:
      - "NEW_BLOCK"
      - "REQUEST_CHAIN"
      - "CHAIN_RESPONSE"
    # add more if you want
    data:
      - payload, depends on type
    sender_id:
      - which node sent this message
    """
    
    type: str
    data: Dict[str, Any]
    sender_id: str
    # optional: add receiver_id if you want direct messages
    # receiver_id: Optional[str] = None

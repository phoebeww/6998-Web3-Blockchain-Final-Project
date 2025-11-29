#!/usr/bin/env bash

# Test script for:
# - tracker interaction
# - single-node voting, mining, results, validation
#
# Assumes:
#   Tracker: uvicorn network.tracker:app --reload --port 9000
#   Node:    uvicorn api.server:app --reload --port 8000

TRACKER_URL="http://localhost:9000"
NODE_URL="http://localhost:8000"

echo "========================================"
echo "  A) Tracker checks"
echo "========================================"

echo "1) Tracker health"
curl -s "${TRACKER_URL}/health"
echo -e "\n"

echo "2) Register node-1 with tracker"
curl -s -X POST "${TRACKER_URL}/register" \
  -H "Content-Type: application/json" \
  -d '{"node_id":"node-1","host":"127.0.0.1","port":8000}'
echo -e "\n"

echo "3) List tracker peers"
curl -s "${TRACKER_URL}/peers"
echo -e "\n"

echo "========================================"
echo "  B) Single-node voting test (node-1)"
echo "========================================"

echo "4) Node health"
curl -s "${NODE_URL}/health"
echo -e "\n"

echo "5) Initial stats"
curl -s "${NODE_URL}/stats"
echo -e "\n"

echo "6) Initial chain (should only have genesis block)"
curl -s "${NODE_URL}/chain"
echo -e "\n"

echo "7) Cast first vote (alice -> Alice)"
curl -s -X POST "${NODE_URL}/vote" \
  -H "Content-Type: application/json" \
  -d '{"voter_id":"alice","choice":"Alice"}'
echo -e "\n"

echo "8) Try duplicate vote (alice -> Alice again)"
curl -s -X POST "${NODE_URL}/vote" \
  -H "Content-Type: application/json" \
  -d '{"voter_id":"alice","choice":"Alice"}'
echo -e "\n"

echo "9) Cast second distinct vote (bob -> Bob)"
curl -s -X POST "${NODE_URL}/vote" \
  -H "Content-Type: application/json" \
  -d '{"voter_id":"bob","choice":"Bob"}'
echo -e "\n"

echo "10) Mine pending votes into a block"
curl -s -X POST "${NODE_URL}/mine"
echo -e "\n"

echo "11) View vote results"
curl -s "${NODE_URL}/results"
echo -e "\n"

echo "12) View full chain"
curl -s "${NODE_URL}/chain"
echo -e "\n"

echo "13) Validate chain integrity"
curl -s "${NODE_URL}/validate"
echo -e "\n"

echo "14) Final stats"
curl -s "${NODE_URL}/stats"
echo -e "\n"

echo "========================================"
echo "Done (tracker + single node test)."
echo "========================================"

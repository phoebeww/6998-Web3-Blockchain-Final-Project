# config.py
"""
Configuration file for the blockchain voting system.
Centralizes all system parameters for easy management and tuning.
"""

# Mining Configuration
# Base difficulty for proof-of-work mining
BASE_DIFFICULTY = 2

# Minimum allowed mining difficulty
MIN_DIFFICULTY = 1

# Maximum allowed mining difficulty
MAX_DIFFICULTY = 5

# Target time between blocks in seconds
TARGET_BLOCK_TIME = 17.5

# Number of blocks to analyze when adjusting difficulty
# Difficulty will only adjust after this many blocks have been mined
DIFFICULTY_ADJUSTMENT_INTERVAL = 3

# Difficulty adjustment thresholds
# If average block time is below this, increase difficulty
DIFFICULTY_INCREASE_THRESHOLD = 15  # seconds

# If average block time is above this, decrease difficulty
DIFFICULTY_DECREASE_THRESHOLD = 20  # seconds

# Stake Configuration
# Initial stake value for new nodes
DEFAULT_STAKE = 0

# Stake reward for successfully mining a valid block
STAKE_REWARD = 1

# Stake penalty for invalid blocks or malicious behavior
STAKE_PENALTY = 2

# Maximum difficulty reduction from stake
# Each 7 stake points reduces difficulty by 1, up to this maximum
MAX_STAKE_INFLUENCE = 2

# Network Configuration
# Tracker URL for peer discovery
DEFAULT_TRACKER_URL = "http://127.0.0.1:9000"

# Timeout for peer connections in seconds
PEER_TIMEOUT = 30

# Interval for heartbeat messages in seconds
HEARTBEAT_INTERVAL = 10

# Voting Configuration
# Default candidate choices
DEFAULT_CANDIDATES = ["Alice", "Bob", "Charlie", "Dave"]

# Maximum number of transactions per block
MAX_TRANSACTIONS_PER_BLOCK = 100


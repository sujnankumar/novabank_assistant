"""
Conversation Memory Configuration
=================================
Centralized settings for SQLite database path and conversation history limits.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Database & History Settings
CONVERSATION_DB_PATH = os.getenv(
    "CONVERSATION_DB_PATH",
    str(PROJECT_ROOT / "data" / "conversations.db"),
)
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

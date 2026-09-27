"""
NovaBank AI Conversation Memory Module (Phase 7)
================================================
Provides persistent SQLite conversation storage, session scoping, chronological history,
customer isolation, and memory-aware orchestrator integration.
"""

from app.memory.config import CONVERSATION_DB_PATH, MAX_HISTORY_MESSAGES
from app.memory.exceptions import (
    ConversationNotFoundError,
    CustomerMismatchError,
    InvalidMessageError,
    MemoryError,
    MemoryStorageError,
)
from app.memory.interface import ConversationMemory
from app.memory.memory_orchestrator import MemoryOrchestrator, run_conversation
from app.memory.models import Conversation, Message
from app.memory.sqlite_memory import SQLiteConversationMemory

__all__ = [
    "CONVERSATION_DB_PATH",
    "MAX_HISTORY_MESSAGES",
    "MemoryError",
    "ConversationNotFoundError",
    "CustomerMismatchError",
    "InvalidMessageError",
    "MemoryStorageError",
    "ConversationMemory",
    "Conversation",
    "Message",
    "SQLiteConversationMemory",
    "MemoryOrchestrator",
    "run_conversation",
]

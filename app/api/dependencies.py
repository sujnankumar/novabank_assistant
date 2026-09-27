"""
API Dependency Injection Providers
==================================
Reusable FastAPI dependencies for ConversationMemory and MemoryOrchestrator.
Facilitates clean unit testing via FastAPI dependency overrides.
Phase 8 Implementation.
"""

from typing import TYPE_CHECKING
from fastapi import Depends
from app.memory.interface import ConversationMemory

if TYPE_CHECKING:
    from app.memory.memory_orchestrator import MemoryOrchestrator


def get_conversation_memory() -> ConversationMemory:
    """Provides a ConversationMemory instance for request handling."""
    from app.memory.sqlite_memory import SQLiteConversationMemory
    return SQLiteConversationMemory()


def get_memory_orchestrator(
    memory: ConversationMemory = Depends(get_conversation_memory),
) -> "MemoryOrchestrator":
    """Provides a MemoryOrchestrator instance wired to the active ConversationMemory."""
    from app.memory.memory_orchestrator import MemoryOrchestrator
    if not isinstance(memory, ConversationMemory):
        memory = get_conversation_memory()
    return MemoryOrchestrator(memory=memory)

"""
Conversation Memory Exceptions
==============================
Typed exception hierarchy for conversation memory operations and storage.
"""


class MemoryError(Exception):
    """Base exception for all conversation memory operations."""
    pass


class ConversationNotFoundError(MemoryError):
    """Raised when a requested conversation ID does not exist."""
    pass


class CustomerMismatchError(MemoryError):
    """Raised when the requesting customer ID does not match the conversation owner."""
    pass


class InvalidMessageError(MemoryError):
    """Raised when a message contains invalid role, empty content, or malformed data."""
    pass


class MemoryStorageError(MemoryError):
    """Raised when an internal SQLite or storage failure occurs."""
    pass

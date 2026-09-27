"""
Test Conversation History Retrieval
===================================
Tests chronological ordering, sliding-window limits, and edge cases.
"""

from pathlib import Path
import pytest

from app.memory.exceptions import ConversationNotFoundError
from app.memory.sqlite_memory import SQLiteConversationMemory


@pytest.fixture
def memory(tmp_path: Path):
    """Provides a fresh SQLiteConversationMemory instance."""
    db_file = tmp_path / "history.db"
    return SQLiteConversationMemory(db_path=db_file, max_history=10)


def test_empty_conversation_history(memory: SQLiteConversationMemory):
    """An empty conversation returns an empty list without raising an error."""
    conv = memory.create_conversation("CUST001")
    history = memory.get_history(conv.conversation_id, "CUST001")
    assert history == []


def test_missing_conversation_history(memory: SQLiteConversationMemory):
    """Attempting to get history for a non-existent conversation raises ConversationNotFoundError."""
    with pytest.raises(ConversationNotFoundError):
        memory.get_history("conv_does_not_exist", "CUST001")


def test_chronological_ordering(memory: SQLiteConversationMemory):
    """Messages are returned strictly in ascending chronological sequence (1, 2, 3...)."""
    conv = memory.create_conversation("CUST001")

    for i in range(1, 6):
        role = "user" if i % 2 != 0 else "assistant"
        memory.add_message(conv.conversation_id, "CUST001", role, f"Message #{i}")

    history = memory.get_history(conv.conversation_id, "CUST001")
    assert len(history) == 5

    seq_nums = [m.sequence_number for m in history]
    assert seq_nums == [1, 2, 3, 4, 5]
    assert [m.content for m in history] == [f"Message #{i}" for i in range(1, 6)]


def test_sliding_window_history_limit(memory: SQLiteConversationMemory):
    """When conversation exceeds limit, latest N messages are returned in chronological order."""
    conv = memory.create_conversation("CUST001")

    # Add 25 messages
    for i in range(1, 26):
        role = "user" if i % 2 != 0 else "assistant"
        memory.add_message(conv.conversation_id, "CUST001", role, f"Message {i}")

    # Request with custom limit of 5
    hist_5 = memory.get_history(conv.conversation_id, "CUST001", limit=5)
    assert len(hist_5) == 5
    # Must be latest 5: 21, 22, 23, 24, 25
    assert [m.sequence_number for m in hist_5] == [21, 22, 23, 24, 25]
    assert [m.content for m in hist_5] == [f"Message {i}" for i in range(21, 26)]

    # Request with default limit (configured as 10)
    hist_default = memory.get_history(conv.conversation_id, "CUST001")
    assert len(hist_default) == 10
    assert [m.sequence_number for m in hist_default] == list(range(16, 26))


def test_history_limit_larger_than_message_count(memory: SQLiteConversationMemory):
    """When limit exceeds the total message count, all messages are returned in order."""
    conv = memory.create_conversation("CUST001")

    memory.add_message(conv.conversation_id, "CUST001", "user", "Message 1")
    memory.add_message(conv.conversation_id, "CUST001", "assistant", "Message 2")

    history = memory.get_history(conv.conversation_id, "CUST001", limit=100)
    assert len(history) == 2
    assert [m.sequence_number for m in history] == [1, 2]


def test_history_limit_zero_or_negative(memory: SQLiteConversationMemory):
    """Requesting limit <= 0 returns an empty list."""
    conv = memory.create_conversation("CUST001")
    memory.add_message(conv.conversation_id, "CUST001", "user", "Hello")

    assert memory.get_history(conv.conversation_id, "CUST001", limit=0) == []
    assert memory.get_history(conv.conversation_id, "CUST001", limit=-5) == []

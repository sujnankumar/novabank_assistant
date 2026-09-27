"""
Test SQLite Conversation Memory
===============================
Tests core CRUD operations, constraint enforcement, and idempotency in SQLiteConversationMemory.
"""

from pathlib import Path
import pytest

from app.memory.exceptions import (
    ConversationNotFoundError,
    CustomerMismatchError,
    InvalidMessageError,
)
from app.memory.sqlite_memory import SQLiteConversationMemory


@pytest.fixture
def memory_db(tmp_path: Path):
    """Provides a fresh SQLiteConversationMemory instance in a temporary directory."""
    db_file = tmp_path / "test_conversations.db"
    return SQLiteConversationMemory(db_path=db_file)


def test_db_initialization_idempotency(tmp_path: Path):
    """Calling initialize_db repeatedly must be safe and not destroy data."""
    db_file = tmp_path / "idempotent.db"
    mem = SQLiteConversationMemory(db_path=db_file)

    # Create conversation and message
    conv = mem.create_conversation("CUST001")
    mem.add_message(conv.conversation_id, "CUST001", "user", "Initial message")

    # Re-run initialization
    mem.initialize_db()
    mem.initialize_db()

    # Data must still be present
    history = mem.get_history(conv.conversation_id, "CUST001")
    assert len(history) == 1
    assert history[0].content == "Initial message"


def test_create_conversation(memory_db: SQLiteConversationMemory):
    """Creating a conversation generates a unique ID, valid timestamps, and persists."""
    conv1 = memory_db.create_conversation("CUST001")
    conv2 = memory_db.create_conversation("CUST001")

    assert conv1.conversation_id.startswith("conv_")
    assert conv2.conversation_id.startswith("conv_")
    assert conv1.conversation_id != conv2.conversation_id
    assert conv1.customer_id == "CUST001"
    assert conv1.created_at is not None
    assert conv1.updated_at is not None


def test_create_conversation_invalid_customer_id(memory_db: SQLiteConversationMemory):
    """Empty customer ID raises CustomerMismatchError."""
    with pytest.raises(CustomerMismatchError):
        memory_db.create_conversation("")

    with pytest.raises(CustomerMismatchError):
        memory_db.create_conversation("   ")


def test_get_conversation(memory_db: SQLiteConversationMemory):
    """Retrieve existing conversation matching customer ID."""
    conv = memory_db.create_conversation("CUST001")
    retrieved = memory_db.get_conversation(conv.conversation_id, "CUST001")

    assert retrieved is not None
    assert retrieved.conversation_id == conv.conversation_id
    assert retrieved.customer_id == "CUST001"


def test_get_conversation_nonexistent(memory_db: SQLiteConversationMemory):
    """Non-existent conversation ID returns None."""
    retrieved = memory_db.get_conversation("nonexistent_id", "CUST001")
    assert retrieved is None


def test_get_conversation_customer_mismatch(memory_db: SQLiteConversationMemory):
    """Querying another customer's conversation returns None."""
    conv = memory_db.create_conversation("CUST001")
    retrieved = memory_db.get_conversation(conv.conversation_id, "CUST002")
    assert retrieved is None


def test_add_messages_and_sequence_ordering(memory_db: SQLiteConversationMemory):
    """Adding messages generates correct monotonic sequence numbers."""
    conv = memory_db.create_conversation("CUST001")
    initial_updated_at = conv.updated_at

    msg1 = memory_db.add_message(conv.conversation_id, "CUST001", "user", "What is my balance?")
    assert msg1.sequence_number == 1
    assert msg1.role == "user"
    assert msg1.content == "What is my balance?"

    msg2 = memory_db.add_message(conv.conversation_id, "CUST001", "assistant", "Your balance is INR 10,000.")
    assert msg2.sequence_number == 2
    assert msg2.role == "assistant"

    msg3 = memory_db.add_message(conv.conversation_id, "CUST001", "user", "What about transactions?")
    assert msg3.sequence_number == 3

    # Conversation updated_at should be updated
    updated_conv = memory_db.get_conversation(conv.conversation_id, "CUST001")
    assert updated_conv.updated_at >= initial_updated_at


def test_add_message_invalid_role(memory_db: SQLiteConversationMemory):
    """Invalid roles must be rejected with InvalidMessageError."""
    conv = memory_db.create_conversation("CUST001")

    with pytest.raises(InvalidMessageError):
        memory_db.add_message(conv.conversation_id, "CUST001", "system", "You are an assistant")

    with pytest.raises(InvalidMessageError):
        memory_db.add_message(conv.conversation_id, "CUST001", "admin", "Perform action")


def test_add_message_empty_content(memory_db: SQLiteConversationMemory):
    """Empty or whitespace content must be rejected with InvalidMessageError."""
    conv = memory_db.create_conversation("CUST001")

    with pytest.raises(InvalidMessageError):
        memory_db.add_message(conv.conversation_id, "CUST001", "user", "")

    with pytest.raises(InvalidMessageError):
        memory_db.add_message(conv.conversation_id, "CUST001", "user", "   \t\n  ")


def test_add_message_nonexistent_conversation(memory_db: SQLiteConversationMemory):
    """Adding a message to a missing conversation raises ConversationNotFoundError."""
    with pytest.raises(ConversationNotFoundError):
        memory_db.add_message("conv_missing", "CUST001", "user", "Hello")


def test_add_message_customer_mismatch(memory_db: SQLiteConversationMemory):
    """Adding a message with mismatched customer ID raises CustomerMismatchError."""
    conv = memory_db.create_conversation("CUST001")

    with pytest.raises(CustomerMismatchError):
        memory_db.add_message(conv.conversation_id, "CUST002", "user", "I am hijacking this conv")

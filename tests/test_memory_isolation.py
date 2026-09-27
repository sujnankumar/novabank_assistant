"""
Test Conversation & Customer Isolation
======================================
Verifies strict isolation boundaries:
- Different conversations remain isolated from each other.
- Cross-customer access attempts fail safely and securely.
"""

from pathlib import Path
import pytest

from app.memory.exceptions import (
    ConversationNotFoundError,
    CustomerMismatchError,
)
from app.memory.sqlite_memory import SQLiteConversationMemory


@pytest.fixture
def memory(tmp_path: Path):
    """Provides a fresh SQLiteConversationMemory instance."""
    db_file = tmp_path / "isolation.db"
    return SQLiteConversationMemory(db_path=db_file)


def test_conversation_isolation_same_customer(memory: SQLiteConversationMemory):
    """Multiple conversations for the same customer remain strictly isolated."""
    conv1 = memory.create_conversation("CUST001")
    conv2 = memory.create_conversation("CUST001")

    # Add messages to conv1
    memory.add_message(conv1.conversation_id, "CUST001", "user", "Message in Conv 1")
    memory.add_message(conv1.conversation_id, "CUST001", "assistant", "Response in Conv 1")

    # Add messages to conv2
    memory.add_message(conv2.conversation_id, "CUST001", "user", "Message in Conv 2")

    # History verification
    history1 = memory.get_history(conv1.conversation_id, "CUST001")
    history2 = memory.get_history(conv2.conversation_id, "CUST001")

    assert len(history1) == 2
    assert [m.content for m in history1] == ["Message in Conv 1", "Response in Conv 1"]

    assert len(history2) == 1
    assert [m.content for m in history2] == ["Message in Conv 2"]


def test_customer_isolation_get_conversation(memory: SQLiteConversationMemory):
    """Customer CUST002 cannot retrieve conversation belonging to CUST001."""
    conv = memory.create_conversation("CUST001")

    # Owner can retrieve
    assert memory.get_conversation(conv.conversation_id, "CUST001") is not None

    # Other customer cannot retrieve
    assert memory.get_conversation(conv.conversation_id, "CUST002") is None


def test_customer_isolation_get_history(memory: SQLiteConversationMemory):
    """Customer CUST002 cannot read message history of CUST001's conversation."""
    conv = memory.create_conversation("CUST001")
    memory.add_message(conv.conversation_id, "CUST001", "user", "Confidential financial query")
    memory.add_message(conv.conversation_id, "CUST001", "assistant", "Confidential account balance")

    # CUST001 can read history
    history = memory.get_history(conv.conversation_id, "CUST001")
    assert len(history) == 2

    # CUST002 receives CustomerMismatchError
    with pytest.raises(CustomerMismatchError):
        memory.get_history(conv.conversation_id, "CUST002")


def test_customer_isolation_add_message(memory: SQLiteConversationMemory):
    """Customer CUST002 cannot inject messages into CUST001's conversation."""
    conv = memory.create_conversation("CUST001")

    with pytest.raises(CustomerMismatchError):
        memory.add_message(
            conv.conversation_id,
            "CUST002",
            "user",
            "Unauthorized injection into CUST001's thread",
        )


def test_cross_customer_multi_conversation_scenario(memory: SQLiteConversationMemory):
    """Two separate customers have independent active conversations with identical queries."""
    conv_a = memory.create_conversation("CUST001")
    conv_b = memory.create_conversation("CUST002")

    memory.add_message(conv_a.conversation_id, "CUST001", "user", "What is my balance?")
    memory.add_message(conv_a.conversation_id, "CUST001", "assistant", "Balance is INR 50,000")

    memory.add_message(conv_b.conversation_id, "CUST002", "user", "What is my balance?")
    memory.add_message(conv_b.conversation_id, "CUST002", "assistant", "Balance is INR 900,000")

    hist_a = memory.get_history(conv_a.conversation_id, "CUST001")
    hist_b = memory.get_history(conv_b.conversation_id, "CUST002")

    assert len(hist_a) == 2
    assert "50,000" in hist_a[1].content
    assert "900,000" not in hist_a[1].content

    assert len(hist_b) == 2
    assert "900,000" in hist_b[1].content
    assert "50,000" not in hist_b[1].content

"""
Test Conversation Memory Persistence
====================================
Tests that conversations and messages survive application restarts and instance re-creation.
"""

from pathlib import Path
from app.memory.sqlite_memory import SQLiteConversationMemory


def test_persistence_across_instance_recreation(tmp_path: Path):
    """
    1. Create database and memory instance A.
    2. Create conversation and add messages.
    3. Destroy/close instance A.
    4. Create instance B pointing to the same SQLite file.
    5. Verify conversation and message history are intact.
    """
    db_file = tmp_path / "persistent_conversations.db"

    # --- Session 1: Create & populate ---
    mem1 = SQLiteConversationMemory(db_path=db_file)
    conv = mem1.create_conversation("CUST001")
    conv_id = conv.conversation_id

    msg1 = mem1.add_message(conv_id, "CUST001", "user", "What is my account balance?")
    msg2 = mem1.add_message(conv_id, "CUST001", "assistant", "Your balance is INR 192,203.99.")
    msg3 = mem1.add_message(conv_id, "CUST001", "user", "What about recent transactions?")

    mem1.close()
    del mem1

    # --- Session 2: Fresh instance (simulating app restart) ---
    mem2 = SQLiteConversationMemory(db_path=db_file)

    # Verify conversation exists
    retrieved_conv = mem2.get_conversation(conv_id, "CUST001")
    assert retrieved_conv is not None
    assert retrieved_conv.conversation_id == conv_id
    assert retrieved_conv.customer_id == "CUST001"
    assert retrieved_conv.created_at == conv.created_at
    assert retrieved_conv.updated_at >= conv.created_at

    # Verify message history persists intact
    history = mem2.get_history(conv_id, "CUST001")
    assert len(history) == 3

    assert history[0].message_id == msg1.message_id
    assert history[0].role == "user"
    assert history[0].content == "What is my account balance?"
    assert history[0].sequence_number == 1

    assert history[1].message_id == msg2.message_id
    assert history[1].role == "assistant"
    assert history[1].content == "Your balance is INR 192,203.99."
    assert history[1].sequence_number == 2

    assert history[2].message_id == msg3.message_id
    assert history[2].role == "user"
    assert history[2].content == "What about recent transactions?"
    assert history[2].sequence_number == 3

    # Add further message in session 2
    msg4 = mem2.add_message(conv_id, "CUST001", "assistant", "Here are your 5 recent transactions.")
    assert msg4.sequence_number == 4

    history_updated = mem2.get_history(conv_id, "CUST001")
    assert len(history_updated) == 4
    assert history_updated[3].sequence_number == 4

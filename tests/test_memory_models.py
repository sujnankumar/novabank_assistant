"""
Test Conversation Memory Models
===============================
Tests Pydantic validation for Conversation and Message schema models.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.memory.models import Conversation, Message


def test_conversation_model_valid():
    """Valid Conversation model initialization."""
    now = datetime.now(timezone.utc).isoformat()
    conv = Conversation(
        conversation_id="conv_12345",
        customer_id="CUST001",
        created_at=now,
        updated_at=now,
    )
    assert conv.conversation_id == "conv_12345"
    assert conv.customer_id == "CUST001"
    assert conv.created_at == now
    assert conv.updated_at == now


def test_conversation_model_missing_fields():
    """Missing required fields raises ValidationError."""
    with pytest.raises(ValidationError):
        Conversation(conversation_id="conv_123")  # missing customer_id, timestamps


def test_message_model_valid_user():
    """Valid user Message model initialization."""
    now = datetime.now(timezone.utc).isoformat()
    msg = Message(
        message_id="msg_001",
        conversation_id="conv_123",
        customer_id="CUST001",
        role="user",
        content="What is my account balance?",
        created_at=now,
        sequence_number=1,
    )
    assert msg.message_id == "msg_001"
    assert msg.role == "user"
    assert msg.sequence_number == 1
    assert msg.content == "What is my account balance?"


def test_message_model_valid_assistant():
    """Valid assistant Message model initialization."""
    now = datetime.now(timezone.utc).isoformat()
    msg = Message(
        message_id="msg_002",
        conversation_id="conv_123",
        customer_id="CUST001",
        role="assistant",
        content="Your account balance is INR 192,203.99.",
        created_at=now,
        sequence_number=2,
    )
    assert msg.message_id == "msg_002"
    assert msg.role == "assistant"
    assert msg.sequence_number == 2


def test_message_model_invalid_role():
    """Roles other than 'user' or 'assistant' are rejected."""
    now = datetime.now(timezone.utc).isoformat()
    invalid_roles = ["system", "admin", "agent", "tool", "function", "bot"]

    for role in invalid_roles:
        with pytest.raises(ValidationError):
            Message(
                message_id="msg_999",
                conversation_id="conv_123",
                customer_id="CUST001",
                role=role,
                content="System prompt",
                created_at=now,
                sequence_number=1,
            )


def test_message_model_empty_content():
    """Empty or whitespace-only content is rejected."""
    now = datetime.now(timezone.utc).isoformat()

    with pytest.raises(ValidationError):
        Message(
            message_id="msg_001",
            conversation_id="conv_123",
            customer_id="CUST001",
            role="user",
            content="",
            created_at=now,
            sequence_number=1,
        )

    with pytest.raises(ValidationError):
        Message(
            message_id="msg_001",
            conversation_id="conv_123",
            customer_id="CUST001",
            role="user",
            content="   \n\t  ",
            created_at=now,
            sequence_number=1,
        )


def test_message_model_invalid_sequence_number():
    """Sequence number must be a positive integer (>= 1)."""
    now = datetime.now(timezone.utc).isoformat()

    with pytest.raises(ValidationError):
        Message(
            message_id="msg_001",
            conversation_id="conv_123",
            customer_id="CUST001",
            role="user",
            content="Valid query",
            created_at=now,
            sequence_number=0,
        )

    with pytest.raises(ValidationError):
        Message(
            message_id="msg_001",
            conversation_id="conv_123",
            customer_id="CUST001",
            role="user",
            content="Valid query",
            created_at=now,
            sequence_number=-1,
        )

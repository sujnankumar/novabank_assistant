"""
Conversation Memory Data Models
===============================
Pydantic schemas representing conversations and individual message turns.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Conversation(BaseModel):
    """Represents a conversational session scoped to a specific customer."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    customer_id: str = Field(..., description="Customer ID owning this conversation")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp of last activity")


class Message(BaseModel):
    """Represents a single message turn within a conversation."""

    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Conversation ID this message belongs to")
    customer_id: str = Field(..., description="Customer ID associated with this message")
    role: Literal["user", "assistant"] = Field(
        ...,
        description="Role of the message sender; strictly 'user' or 'assistant'",
    )
    content: str = Field(..., description="Conversational text content")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    sequence_number: int = Field(
        ...,
        ge=1,
        description="Monotonically increasing sequence number within conversation",
    )
    sources: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Retrieved sources or citations for assistant messages",
    )
    thought_process: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Step-by-step thinking process for assistant messages",
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="Execution duration in milliseconds",
    )

    @field_validator("content")
    @classmethod
    def validate_content_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty or whitespace only.")
        return v

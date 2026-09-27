"""
Conversation Schemas
====================
Pydantic schemas for conversation creation and history retrieval endpoints.
Phase 8 Implementation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CreateConversationRequest(BaseModel):
    """Request payload for creating a new conversation."""

    customer_id: str = Field(..., description="Customer ID associated with the conversation")

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("customer_id cannot be empty or whitespace only.")
        return v.strip()


class ConversationResponse(BaseModel):
    """Response returned upon successful conversation creation."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    customer_id: str = Field(..., description="Customer ID owning this conversation")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp of last activity")


class MessageResponse(BaseModel):
    """Representation of an individual message turn in conversation history."""

    message_id: str = Field(..., description="Unique message identifier")
    role: str = Field(..., description="Role of the sender ('user' or 'assistant')")
    content: str = Field(..., description="Conversational text content")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    sequence_number: int = Field(..., description="Chronological sequence number within conversation")
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


class ConversationHistoryResponse(BaseModel):
    """Response payload returning chronological messages for a conversation."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    customer_id: str = Field(..., description="Customer ID owning this conversation")
    messages: List[MessageResponse] = Field(
        default_factory=list,
        description="Chronological list of conversation messages",
    )


class ConversationSummary(BaseModel):
    """Summary of a past conversation session for history listing in the sidebar."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    customer_id: str = Field(..., description="Customer ID owning this conversation")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp of last activity")
    title: str = Field(default="New Conversation", description="Preview title from first user query")
    message_count: int = Field(default=0, description="Total messages in this conversation")
    last_message: str | None = Field(default=None, description="Preview of latest message content")


class ConversationListResponse(BaseModel):
    """Response payload returning list of conversations owned by the customer."""

    customer_id: str = Field(..., description="Customer ID")
    conversations: List[ConversationSummary] = Field(
        default_factory=list,
        description="List of conversations ordered by most recent activity",
    )

"""
Chat Schemas
============
Pydantic schemas for the RESTful chat endpoint.
Phase 8 Implementation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Request payload for sending a chat message to the assistant."""

    conversation_id: str = Field(..., description="Existing conversation identifier")
    customer_id: str = Field(..., description="Trusted customer identifier")
    message: str = Field(..., description="User natural language banking query")

    @field_validator("conversation_id")
    @classmethod
    def validate_conv_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("conversation_id cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("customer_id")
    @classmethod
    def validate_cust_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("customer_id cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("message cannot be empty or whitespace only.")
        return v.strip()


class ChatResponse(BaseModel):
    """Response payload returned from the assistant."""

    conversation_id: str = Field(..., description="Conversation identifier")
    customer_id: str = Field(..., description="Customer identifier")
    message: str = Field(..., description="Assistant response content")
    route: Optional[str] = Field(None, description="Routing classification (TOOL, RAG, BOTH, etc.)")
    sources: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Source provenance references (tools or policy documents)",
    )
    thought_process: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Chronological agent reasoning and execution steps",
    )
    execution_time_ms: Optional[float] = Field(
        None,
        description="Total orchestrator execution time in milliseconds",
    )


class ErrorDetail(BaseModel):
    """Structured error detail representation."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")


class ErrorResponse(BaseModel):
    """Client-facing structured error response."""

    error: ErrorDetail = Field(..., description="Error detail container")

"""
RAG Pipeline Data Schemas
=========================
Pydantic schemas for documents, chunks, metadata, and retrieval results.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Raw knowledge-base document loaded from disk."""

    content: str = Field(..., description="Full text content of document")
    source: str = Field(..., description="Filename of source document (e.g. 01_home_loan_policy.md)")
    document_id: str = Field(..., description="Unique identifier for the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata from metadata.json")


class DocumentChunk(BaseModel):
    """Individual chunk extracted from a knowledge-base document."""

    chunk_id: str = Field(..., description="Unique chunk identifier (e.g. 01_home_loan_policy_chunk_001)")
    content: str = Field(..., description="Text content of this chunk")
    source: str = Field(..., description="Source filename")
    document_id: str = Field(..., description="Document identifier")
    section: Optional[str] = Field(None, description="Section or heading title")
    chunk_index: int = Field(..., ge=0, description="Sequential index of this chunk within the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document & chunk metadata")


class RetrievalItem(BaseModel):
    """Single matching chunk in retrieval result."""

    chunk_id: str = Field(..., description="Matching chunk ID")
    content: str = Field(..., description="Text content of the retrieved chunk")
    score: float = Field(..., description="Cosine similarity score (0.0 - 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source and section metadata")


class RetrievalResponse(BaseModel):
    """Structured retrieval response."""

    query: str = Field(..., description="The user query")
    retrieved: bool = Field(..., description="Whether any relevant results above threshold were found")
    results: List[RetrievalItem] = Field(default_factory=list, description="Ranked list of matching chunks")

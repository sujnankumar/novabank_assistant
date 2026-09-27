"""
Agent State Schema
==================
Defines the central LangGraph state structure for the NovaBank AI Orchestrator.
"""

import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Central state representation passed through all LangGraph orchestrator nodes."""

    # Thinking & execution traceability
    thought_steps: Annotated[List[Dict[str, Any]], operator.add]

    # Input parameters
    query: str
    customer_id: Optional[str]

    # Routing
    route: Optional[str]  # "TOOL" | "RAG" | "BOTH" | "CLARIFICATION" | "UNSUPPORTED"

    # Tool invocation
    selected_tools: List[str]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]

    # RAG retrieval
    rag_results: List[Dict[str, Any]]

    # Unified context with source provenance
    context: List[Dict[str, Any]]

    # Response generation
    response: Optional[str]
    status: str  # "success" | "needs_customer_context" | "unsupported" | "error"
    sources: List[Dict[str, Any]]

    # Execution tracking & safety
    error: Optional[Dict[str, Any]]
    run_id: str
    step_count: int
    tool_count: int

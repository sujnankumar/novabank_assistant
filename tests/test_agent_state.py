"""
Test Agent State Schema
=======================
Tests for AgentState TypedDict structure, required/optional fields, and state transitions.
"""

import pytest
from app.agents.state import AgentState


def test_agent_state_creation_and_fields():
    """Verify AgentState can be constructed with all specified fields."""
    state: AgentState = {
        "query": "What is my account balance?",
        "customer_id": "CUST001",
        "route": "TOOL",
        "selected_tools": ["get_balance"],
        "tool_calls": [{"name": "get_balance", "args": {"customer_id": "CUST001"}}],
        "tool_results": [{"source_type": "tool", "source": "get_balance", "success": True, "data": {"total_balance": 5000}}],
        "rag_results": [],
        "context": [{"source_type": "tool", "source": "get_balance", "data": {"total_balance": 5000}}],
        "response": "Your balance is INR 5,000.00.",
        "status": "success",
        "sources": [{"type": "tool", "name": "get_balance"}],
        "error": None,
        "run_id": "run_test_001",
        "step_count": 4,
        "tool_count": 1,
    }

    assert state["query"] == "What is my account balance?"
    assert state["customer_id"] == "CUST001"
    assert state["route"] == "TOOL"
    assert len(state["selected_tools"]) == 1
    assert state["status"] == "success"
    assert state["step_count"] == 4


def test_agent_state_partial_initialization():
    """Verify AgentState can be initialized with minimal starting fields."""
    state: AgentState = {
        "query": "What are home loan rates?",
        "customer_id": None,
        "run_id": "run_test_002",
        "step_count": 0,
        "tool_count": 0,
    }

    assert state["query"] == "What are home loan rates?"
    assert state["customer_id"] is None
    assert state.get("route") is None
    assert state.get("tool_results") is None

"""
Test Banking Orchestrator End-to-End
====================================
Tests for full LangGraph orchestrator execution, node sequencing, response schemas,
step limits, and status codes across TOOL, RAG, BOTH, and CLARIFICATION flows.
"""

from unittest.mock import MagicMock
import pytest
from app.agents.orchestrator import BankingOrchestrator
from app.agents.rag_executor import RAGExecutor


@pytest.fixture
def orchestrator():
    return BankingOrchestrator()


def test_orchestrator_tool_flow(orchestrator):
    """Orchestrator executes TOOL flow and returns matching Section 52 schema."""
    res = orchestrator.run("What is my balance?", customer_id="CUST001")

    assert res["status"] == "success"
    assert res["route"] == "TOOL"
    assert isinstance(res["response"], str)
    assert "192,203.99" in res["response"]
    assert len(res["sources"]) == 1
    assert res["sources"][0]["type"] == "tool"
    assert res["sources"][0]["name"] == "get_balance"


def test_orchestrator_rag_flow(orchestrator):
    """Orchestrator executes RAG flow and returns grounded response with sources."""
    res = orchestrator.run("What are the home loan eligibility requirements?")

    assert res["status"] == "success"
    assert res["route"] == "RAG"
    assert isinstance(res["response"], str)
    assert len(res["sources"]) > 0
    assert all(s["type"] == "rag" for s in res["sources"])
    assert any("home_loan" in s["source"] for s in res["sources"])


def test_orchestrator_both_flow(orchestrator):
    """Orchestrator executes BOTH flow and returns sources from both tool and rag."""
    res = orchestrator.run(
        "What is my current balance and what is the minimum balance requirement?",
        customer_id="CUST001",
    )

    assert res["status"] == "success"
    assert res["route"] == "BOTH"
    types = [s["type"] for s in res["sources"]]
    assert "tool" in types
    assert "rag" in types


def test_orchestrator_missing_customer_id_flow(orchestrator):
    """Orchestrator returns needs_customer_context status when customer ID is absent for tool queries."""
    res = orchestrator.run("What is my balance?", customer_id=None)

    assert res["status"] == "needs_customer_context"
    assert res["route"] == "CLARIFICATION"
    assert "Customer identification is required" in res["response"]
    assert res["sources"] == []


def test_orchestrator_unsupported_flow(orchestrator):
    """Orchestrator returns unsupported status for out-of-domain queries."""
    res = orchestrator.run("Can you write a poem about quantum computers?")

    assert res["status"] == "unsupported"
    assert res["route"] == "UNSUPPORTED"
    assert "cannot answer" in res["response"].lower()
    assert res["sources"] == []


def test_orchestrator_empty_query_flow(orchestrator):
    """Orchestrator handles empty queries safely without throwing exceptions."""
    res = orchestrator.run("")
    assert res["status"] == "unsupported"
    assert res["route"] == "UNSUPPORTED"
    assert res["response"] == "Query cannot be empty."


def test_orchestrator_step_limit_loop_protection():
    """Graph step limit protects against runaway execution loops."""
    # Force step limit to 1 step
    short_orchestrator = BankingOrchestrator(max_steps=1)
    res = short_orchestrator.run("What is my balance?", customer_id="CUST001")

    # Should hit limit and exit safely
    assert res["status"] in ["error", "unsupported"]

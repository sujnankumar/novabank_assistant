"""
Test Mixed Queries (BOTH Route)
===============================
Tests for queries that simultaneously require customer-specific data and general bank policy.
"""

from unittest.mock import MagicMock
import pytest
from app.agents.context_validator import ContextValidator
from app.agents.orchestrator import BankingOrchestrator
from app.agents.rag_executor import RAGExecutor


def test_mixed_query_invokes_both_tool_and_rag():
    """Verify mixed query executes Banking Tool AND RAG, populating both sources in output."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = {
        "query": "What is my current balance and what is the minimum balance requirement?",
        "retrieved": True,
        "results": [
            {
                "chunk_id": "06_savings_chunk_005",
                "content": "Basic Savings minimum balance is INR 1,000.",
                "score": 0.85,
                "metadata": {
                    "source": "06_savings_account_policy.md",
                    "section": "6. Minimum Balance Requirements",
                },
            }
        ],
    }

    rag_exec = RAGExecutor(retriever=mock_retriever)
    orchestrator = BankingOrchestrator(rag_executor=rag_exec)

    query = "What is my current balance and what is the minimum balance requirement?"
    result = orchestrator.run(query, customer_id="CUST001")

    assert result["status"] == "success"
    assert result["route"] == "BOTH"

    # Verify both sources present
    source_types = [s["type"] for s in result["sources"]]
    assert "tool" in source_types
    assert "rag" in source_types

    # Verify tool name and rag document name
    assert any(s.get("name") == "get_balance" for s in result["sources"])
    assert any(s.get("source") == "06_savings_account_policy.md" for s in result["sources"])

    # Verify response text combines both facts
    assert "1,92,203.99" in result["response"] or "192,203.99" in result["response"] or "192203.99" in result["response"].replace(",", "")
    assert "minimum balance" in result["response"].lower() or "1,000" in result["response"]


def test_mixed_query_without_customer_id_requires_clarification():
    """Mixed query lacking customer ID requests clarification rather than partial execution."""
    orchestrator = BankingOrchestrator()
    query = "What is my balance and what is the minimum balance requirement?"
    result = orchestrator.run(query, customer_id=None)

    assert result["status"] == "needs_customer_context"
    assert result["route"] == "CLARIFICATION"
    assert "Customer identification is required" in result["response"]
    assert result["sources"] == []

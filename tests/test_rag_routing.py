"""
Test RAG Retrieval Execution
============================
Tests for RAGExecutor invoking Phase 5 retriever, preserving source provenance,
and handling empty or erroneous retrievals safely.
"""

from unittest.mock import MagicMock
import pytest
from app.agents.rag_executor import RAGExecutor


def test_rag_retrieval_success_with_provenance():
    """Verify RAGExecutor structures chunks with source, section, score, and content."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = {
        "query": "home loan requirements",
        "retrieved": True,
        "results": [
            {
                "chunk_id": "01_home_loan_policy_chunk_009",
                "content": "Age requirement between 21 and 60 years.",
                "score": 0.7295,
                "metadata": {
                    "source": "01_home_loan_policy.md",
                    "document_id": "HOME_LOAN_POLICY",
                    "section": "4.1 Age Requirements",
                },
            }
        ],
    }

    executor = RAGExecutor(retriever=mock_retriever, top_k=3)
    results = executor.retrieve("What are home loan requirements?")

    assert len(results) == 1
    item = results[0]
    assert item["source_type"] == "rag"
    assert item["source"] == "01_home_loan_policy.md"
    assert item["section"] == "4.1 Age Requirements"
    assert item["score"] == 0.7295
    assert "21 and 60 years" in item["content"]
    mock_retriever.retrieve.assert_called_once_with(query="What are home loan requirements?", top_k=3)


def test_rag_retrieval_empty_results():
    """Verify RAGExecutor returns an empty list when no documents match threshold."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = {
        "query": "alien propulsion",
        "retrieved": False,
        "results": [],
    }

    executor = RAGExecutor(retriever=mock_retriever)
    results = executor.retrieve("alien propulsion")
    assert results == []


def test_rag_retrieval_exception_handled():
    """Verify RAGExecutor captures unexpected exceptions without raising and crashing."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.side_effect = RuntimeError("Qdrant connection timeout")

    executor = RAGExecutor(retriever=mock_retriever)
    results = executor.retrieve("test query")

    assert len(results) == 1
    assert results[0]["source_type"] == "rag"
    assert "error" in results[0]
    assert results[0]["error"]["type"] == "rag_exception"

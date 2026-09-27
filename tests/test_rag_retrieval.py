"""
Test RAG Retrieval Pipeline
===========================
End-to-end tests for the RAG retriever:
  - Known banking queries retrieve relevant policy documents
  - No-result behavior and similarity threshold filtering
  - Chunk metadata completeness (chunk_id, source, document_id, section, score)
  - Input validation (empty query, non-positive top_k)
  - Reproducibility across multiple queries
"""

import pytest
from app.rag.retriever import RAGRetriever


@pytest.fixture(scope="module")
def retriever():
    """Shared retriever instance with index built/loaded."""
    r = RAGRetriever()
    if not r.is_index_ready():
        r.build_index()
    return r


def test_home_loan_query_retrieval(retriever):
    """Query about home loan eligibility retrieves home loan policy."""
    query = "What are the eligibility requirements for a home loan?"
    res = retriever.retrieve(query, top_k=3)

    assert res["retrieved"] is True
    assert len(res["results"]) > 0

    sources = [r["metadata"]["source"] for r in res["results"]]
    assert any("01_home_loan_policy.md" in s for s in sources)

    top_result = res["results"][0]
    assert "chunk_id" in top_result
    assert "content" in top_result
    assert "score" in top_result
    assert top_result["score"] >= 0.35


def test_fixed_deposit_query_retrieval(retriever):
    """Query about fixed deposit rates and tenure retrieves fixed deposit policy."""
    query = "What is the fixed deposit policy and interest rates?"
    res = retriever.retrieve(query, top_k=3)

    assert res["retrieved"] is True
    sources = [r["metadata"]["source"] for r in res["results"]]
    assert any("07_fixed_deposit_policy.md" in s for s in sources)


def test_fraud_reporting_query_retrieval(retriever):
    """Query about reporting fraud retrieves fraud or transaction security policy."""
    query = "How do I report a fraudulent transaction?"
    res = retriever.retrieve(query, top_k=3)

    assert res["retrieved"] is True
    sources = [r["metadata"]["source"] for r in res["results"]]
    assert any(
        s in ["10_fraud_and_security_policy.md", "08_transaction_policy.md"]
        for s in sources
    )


def test_savings_account_query_retrieval(retriever):
    """Query about savings account rules retrieves savings account policy."""
    query = "What are the rules and minimum balance for a savings account?"
    res = retriever.retrieve(query, top_k=3)

    assert res["retrieved"] is True
    sources = [r["metadata"]["source"] for r in res["results"]]
    assert any("06_savings_account_policy.md" in s for s in sources)


def test_vehicle_loan_query_retrieval(retriever):
    """Query about vehicle loan requirements retrieves vehicle loan policy."""
    query = "What are the requirements for a vehicle loan?"
    res = retriever.retrieve(query, top_k=3)

    assert res["retrieved"] is True
    sources = [r["metadata"]["source"] for r in res["results"]]
    assert any("04_vehicle_loan_policy.md" in s for s in sources)


def test_no_result_outside_domain_query(retriever):
    """Query completely outside banking domain with high threshold returns empty."""
    query = "quantum electrodynamics of alien spacecraft propulsion in deep space"
    res = retriever.retrieve(query, top_k=5, threshold=0.75)

    assert res["retrieved"] is False
    assert res["results"] == []


def test_result_structure_and_ordering(retriever):
    """Retrieved results must have descending scores and complete metadata."""
    query = "What documents are required to apply for personal loans?"
    res = retriever.retrieve(query, top_k=5)

    assert res["retrieved"] is True
    results = res["results"]
    assert len(results) <= 5

    # Check descending order
    for i in range(len(results) - 1):
        assert results[i]["score"] >= results[i + 1]["score"]

    # Check schema completeness
    for item in results:
        assert "chunk_id" in item
        assert "content" in item
        assert "score" in item
        assert "metadata" in item
        assert "source" in item["metadata"]
        assert "document_id" in item["metadata"]


def test_query_validation_errors(retriever):
    """Empty queries or invalid top_k raise ValueError."""
    with pytest.raises(ValueError):
        retriever.retrieve("")

    with pytest.raises(ValueError):
        retriever.retrieve("   ")

    with pytest.raises(ValueError):
        retriever.retrieve("valid query", top_k=0)

    with pytest.raises(ValueError):
        retriever.retrieve("valid query", top_k=-5)


def test_reproducibility(retriever):
    """Same query produces identical results and ordering."""
    query = "How to close a dormant account?"
    res1 = retriever.retrieve(query, top_k=3)
    res2 = retriever.retrieve(query, top_k=3)

    assert res1["retrieved"] == res2["retrieved"]
    assert len(res1["results"]) == len(res2["results"])

    for r1, r2 in zip(res1["results"], res2["results"]):
        assert r1["chunk_id"] == r2["chunk_id"]
        assert pytest.approx(r1["score"], abs=1e-4) == r2["score"]

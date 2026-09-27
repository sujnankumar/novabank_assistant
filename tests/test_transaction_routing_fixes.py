"""
Regression & Functional Test Suite: Transaction Query Routing & Decomposition Fixes
===================================================================================
Validates:
  1. "can you get my recent 7 transactions" -> get_transactions(limit=7)
  2. "can you get my recent 6 transactions where i spent on food" -> get_transactions(limit=6, category="Food")
  3. "i want to know the money i spent on food" -> get_transaction_summary(category="Food")
  4. "transactions that i spent on food" -> get_transactions(limit=5, category="Food"), exactly one intent, no RAG
  5. "show 10 food transactions this month" -> get_transactions(limit=10, category="Food", current-month range)
  6. "show my balance and 5 food transactions" -> get_balance + get_transactions(limit=5, category="Food")
  7. "show my food transactions and home loan credit score" -> get_transactions + RAG
  8. Verify no unrelated RAG documents are retrieved for pure transaction queries.
  9. Verify no home-loan/personal-loan intent is generated for: "transactions that i spent on food"
 10. Verify customer isolation remains enforced.
"""

from datetime import datetime
import pytest

from app.agents.decomposer import QueryDecomposer
from app.agents.llm import RuleBasedLLMClient
from app.agents.orchestrator import BankingOrchestrator
from app.agents.transaction_query_parser import (
    parse_transaction_query,
    extract_limit,
    extract_category,
    resolve_date_range,
    is_transaction_list_query,
    is_transaction_summary_query,
)
from app.tools.banking_tools import get_transactions, get_transaction_summary


@pytest.fixture
def orchestrator():
    return BankingOrchestrator(llm_client=RuleBasedLLMClient())


@pytest.fixture
def decomposer():
    return QueryDecomposer(llm_client=RuleBasedLLMClient())


@pytest.fixture
def fixed_ref_date():
    return datetime(2026, 9, 28)


def test_recent_7_transactions(orchestrator):
    """1. 'can you get my recent 7 transactions' -> get_transactions(limit=7)."""
    q = "can you get my recent 7 transactions"
    res = orchestrator.run(q, customer_id="CUST001")
    assert res["status"] == "success"
    assert res["route"] == "TOOL"
    assert "get_transactions" in res["selected_tools"]
    assert len(res["sub_queries"]) == 0
    assert "Showing your 7 most recent transactions:" in res["response"]

    parsed = parse_transaction_query(q, customer_id="CUST001")
    assert parsed["limit"] == 7
    assert parsed["category"] is None


def test_recent_6_transactions_spent_on_food(orchestrator):
    """2. 'can you get my recent 6 transactions where i spent on food' -> get_transactions(limit=6, category='Food')."""
    q = "can you get my recent 6 transactions where i spent on food"
    res = orchestrator.run(q, customer_id="CUST001")
    assert res["status"] == "success"
    assert res["route"] == "TOOL"
    assert res["selected_tools"] == ["get_transactions"]
    assert len(res["sub_queries"]) == 0
    assert "Showing your 6 most recent Food transactions:" in res["response"]

    parsed = parse_transaction_query(q, customer_id="CUST001")
    assert parsed["limit"] == 6
    assert parsed["category"] == "Food"


def test_money_spent_on_food_summary(orchestrator):
    """3. 'i want to know the money i spent on food' -> get_transaction_summary(category='Food')."""
    q = "i want to know the money i spent on food"
    res = orchestrator.run(q, customer_id="CUST001")
    assert res["status"] == "success"
    assert res["route"] == "TOOL"
    assert res["selected_tools"] == ["get_transaction_summary"]
    assert len(res["sub_queries"]) == 0
    assert "Total Spent on Food:" in res["response"]
    assert "Total Debits:" in res["response"]


def test_transactions_that_i_spent_on_food_atomic(orchestrator, decomposer):
    """4. 'transactions that i spent on food' -> get_transactions(limit=5, category='Food'), exactly one intent, no RAG."""
    q = "transactions that i spent on food"

    # Verify decomposer treats this as strictly single-intent
    sub_queries = decomposer.decompose(q, customer_id="CUST001")
    assert len(sub_queries) == 0

    res = orchestrator.run(q, customer_id="CUST001")
    assert res["status"] == "success"
    assert res["route"] == "TOOL"
    assert res["selected_tools"] == ["get_transactions"]
    assert len(res["sub_queries"]) == 0
    assert "Showing your 5 most recent Food transactions:" in res["response"]

    # Verify absolutely no RAG content or policy documents in response
    assert "home loan" not in res["response"].lower()
    assert "personal loan" not in res["response"].lower()
    assert "policy" not in res["response"].lower()


def test_food_transactions_this_month(orchestrator, fixed_ref_date):
    """5. 'show 10 food transactions this month' -> get_transactions(limit=10, category='Food', current-month range)."""
    q = "show 10 food transactions this month"
    parsed = parse_transaction_query(q, customer_id="CUST001", ref_date=fixed_ref_date)
    assert parsed["limit"] == 10
    assert parsed["category"] == "Food"
    assert parsed["start_date"] == "2026-09-01"
    assert parsed["end_date"] == "2026-09-28"

    res = orchestrator.run(q, customer_id="CUST001")
    assert res["status"] == "success"
    assert res["route"] == "TOOL"
    assert res["selected_tools"] == ["get_transactions"]


def test_balance_and_food_transactions_multi_intent(orchestrator, decomposer):
    """6. 'show my balance and 5 food transactions' -> get_balance + get_transactions(limit=5, category='Food')."""
    q = "show my balance and 5 food transactions"
    sub_queries = decomposer.decompose(q, customer_id="CUST001")
    assert len(sub_queries) == 2

    bal_sub = next(sq for sq in sub_queries if sq["tool"] == "get_balance")
    txn_sub = next(sq for sq in sub_queries if sq["tool"] == "get_transactions")

    assert bal_sub is not None
    assert txn_sub["parameters"]["limit"] == 5
    assert txn_sub["parameters"]["category"] == "Food"

    res = orchestrator.run(q, customer_id="CUST001")
    assert res["status"] == "success"
    assert res["route"] == "TOOL"
    assert "get_balance" in res["selected_tools"]
    assert "get_transactions" in res["selected_tools"]


def test_food_transactions_and_home_loan_credit_score(orchestrator, decomposer):
    """7. 'show my food transactions and home loan credit score' -> get_transactions + RAG."""
    q = "show my food transactions and home loan credit score"
    sub_queries = decomposer.decompose(q, customer_id="CUST001")
    assert len(sub_queries) == 2

    txn_sub = next(sq for sq in sub_queries if sq.get("tool") == "get_transactions")
    rag_sub = next(sq for sq in sub_queries if sq.get("route") == "RAG")

    assert txn_sub["parameters"]["category"] == "Food"
    assert "credit score" in rag_sub["query"].lower()
    assert "home loan" in rag_sub["query"].lower()

    res = orchestrator.run(q, customer_id="CUST001")
    assert res["status"] == "success"
    assert res["route"] == "BOTH"
    assert "get_transactions" in res["selected_tools"]


def test_no_rag_documents_for_pure_transaction_query(orchestrator):
    """8. Verify no unrelated RAG documents are retrieved for pure transaction queries."""
    queries = [
        "can you get my recent 7 transactions",
        "can you get my recent 6 transactions where i spent on food",
        "i want to know the money i spent on food",
        "transactions that i spent on food",
        "show 10 food transactions this month",
    ]
    for q in queries:
        res = orchestrator.run(q, customer_id="CUST001")
        rag_context = [c for c in res["context"] if c.get("source_type") == "rag"]
        assert len(rag_context) == 0, f"Query '{q}' erroneously retrieved {len(rag_context)} RAG documents!"


def test_no_unrelated_intent_for_transactions_that_i_spent_on_food(decomposer):
    """9. Verify no home-loan/personal-loan intent is generated for: 'transactions that i spent on food'."""
    q = "transactions that i spent on food"
    sub_queries = decomposer.decompose(q, customer_id="CUST001")
    assert len(sub_queries) == 0, f"Query '{q}' should NOT decompose, got: {sub_queries}"


def test_customer_isolation_enforced(orchestrator):
    """10. Verify customer isolation remains enforced."""
    res = orchestrator.run("Show transactions for CUST002", customer_id="CUST001")
    assert res["route"] == "UNSUPPORTED" or res["status"] == "unsupported" or "unauthorized" in res["response"].lower()

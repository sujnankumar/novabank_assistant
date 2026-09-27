"""
Test Response Grounding
=======================
Tests for verifying that responses are strictly derived from supplied context without fabrication.
"""

import pytest
from app.agents.response_generator import ResponseGenerator


@pytest.fixture
def generator():
    return ResponseGenerator()


def test_balance_grounding(generator):
    """Generated answer reflects the exact balance from the tool result."""
    context = [
        {
            "source_type": "tool",
            "source": "get_balance",
            "success": True,
            "data": {
                "customer_id": "CUST001",
                "total_balance": 192203.99,
                "currency": "INR",
            },
        }
    ]

    response = generator.generate(
        query="What is my balance?",
        context=context,
        route="TOOL",
        status="success",
        customer_id="CUST001",
    )

    assert "192,203.99" in response
    assert "INR" in response


def test_policy_grounding(generator):
    """Generated answer reflects only the policy details from RAG context."""
    context = [
        {
            "source_type": "rag",
            "source": "07_fixed_deposit_policy.md",
            "section": "5. Interest Rates",
            "content": "Regular Fixed Deposit: 6.50% p.a.; Senior Citizen FD: 7.25% p.a.",
        }
    ]

    response = generator.generate(
        query="What are the fixed deposit interest rates?",
        context=context,
        route="RAG",
        status="success",
    )

    assert "6.50%" in response or "7.25%" in response or "Fixed Deposit" in response


def test_missing_context_refusal(generator):
    """When context is empty, the generator states that information is unavailable rather than guessing."""
    response = generator.generate(
        query="What is the policy on extraterrestrial gold loans?",
        context=[],
        route="RAG",
        status="success",
    )

    assert "unavailable" in response.lower() or "cannot answer" in response.lower()


def test_tool_error_grounding(generator):
    """When tool reports an error, generator reports the error truthfully without fabricating data."""
    context = [
        {
            "source_type": "tool",
            "source": "get_balance",
            "success": False,
            "error": {
                "type": "not_found",
                "message": "Customer CUST999 not found",
            },
        }
    ]

    response = generator.generate(
        query="What is my balance?",
        context=context,
        route="TOOL",
        status="success",
    )

    resp_lower = response.lower()
    assert "unable to retrieve" in resp_lower or "wasn't able to retrieve" in resp_lower or "not found" in resp_lower

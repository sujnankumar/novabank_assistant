"""
Test Tool Execution & Routing
=============================
Tests for tool execution, parameter injection protections, tool call limits, and error handling.
"""

import pytest
from app.agents.tools_executor import ToolsExecutor


def test_tool_execution_success():
    """Verify tool executes and outputs structured result with source provenance."""
    executor = ToolsExecutor()
    tool_calls = [{"name": "get_balance", "args": {"customer_id": "CUST001"}}]

    res = executor.execute_tools(tool_calls, trusted_customer_id="CUST001")
    assert res["new_tool_count"] == 1
    assert len(res["tool_results"]) == 1

    item = res["tool_results"][0]
    assert item["source_type"] == "tool"
    assert item["source"] == "get_balance"
    assert item["success"] is True
    assert "total_balance" in item["data"]


def test_tool_execution_enforces_trusted_customer_id():
    """Verify user-provided customer_id in arguments is overridden by trusted customer_id."""
    executor = ToolsExecutor()
    # Attempting to query CUST002 with trusted ID CUST001
    tool_calls = [{"name": "get_balance", "args": {"customer_id": "CUST002"}}]

    res = executor.execute_tools(tool_calls, trusted_customer_id="CUST001")
    assert res["tool_results"][0]["success"] is True
    # Verify the customer returned is CUST001, NOT CUST002
    assert res["tool_results"][0]["data"]["customer_id"] == "CUST001"


def test_tool_execution_without_trusted_customer_id_fails_safely():
    """Customer-specific tool without trusted customer ID returns error result, not crash."""
    executor = ToolsExecutor()
    tool_calls = [{"name": "get_balance", "args": {}}]

    res = executor.execute_tools(tool_calls, trusted_customer_id=None)
    assert res["tool_results"][0]["success"] is False
    assert res["tool_results"][0]["error"]["type"] == "missing_customer_context"


def test_tool_call_limit_enforced():
    """Exceeding MAX_TOOL_CALLS halts further executions and logs limit_exceeded error."""
    executor = ToolsExecutor(max_tool_calls=2)
    tool_calls = [
        {"name": "get_balance", "args": {"customer_id": "CUST001"}},
        {"name": "get_accounts", "args": {"customer_id": "CUST001"}},
        {"name": "get_customer_profile", "args": {"customer_id": "CUST001"}},
    ]

    res = executor.execute_tools(tool_calls, trusted_customer_id="CUST001")
    assert len(res["tool_results"]) == 3
    assert res["tool_results"][0]["success"] is True
    assert res["tool_results"][1]["success"] is True
    assert res["tool_results"][2]["success"] is False
    assert res["tool_results"][2]["error"]["type"] == "limit_exceeded"


def test_unknown_tool_fails_gracefully():
    """Invoking an unregistered tool name returns an unknown_tool error safely."""
    executor = ToolsExecutor()
    tool_calls = [{"name": "execute_arbitrary_shell", "args": {}}]

    res = executor.execute_tools(tool_calls, trusted_customer_id="CUST001")
    assert res["tool_results"][0]["success"] is False
    assert res["tool_results"][0]["error"]["type"] == "unknown_tool"

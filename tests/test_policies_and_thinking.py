"""
Test Policy Endpoints and Thought Process Serialization
======================================================
Tests for:
  - GET /api/policies (listing official policies)
  - GET /api/policies/{filename} (policy document details and markdown retrieval)
  - GET /api/policies/{document_id} (retrieval by document ID)
  - 404 on nonexistent policy document
  - POST /api/chat including thought_process and execution_time_ms
"""

from fastapi.testclient import TestClient
from app.main import app


def test_list_policies():
    """GET /api/policies returns 200 with list of available NovaBank policy documents."""
    with TestClient(app) as client:
        res = client.get("/api/policies")
        assert res.status_code == 200
        policies = res.json()
        assert isinstance(policies, list)
        assert len(policies) >= 10

        # Check for key policy files
        filenames = [p.get("filename") for p in policies]
        assert "01_home_loan_policy.md" in filenames
        assert "06_savings_account_policy.md" in filenames
        assert any(p.get("document_id") == "HOME_LOAN_POLICY" for p in policies)


def test_get_policy_by_filename():
    """GET /api/policies/{filename} returns complete markdown content and sections."""
    with TestClient(app) as client:
        res = client.get("/api/policies/06_savings_account_policy.md")
        assert res.status_code == 200
        data = res.json()
        assert data["filename"] == "06_savings_account_policy.md"
        assert "Savings Account" in data["title"]
        assert len(data["content"]) > 100
        assert isinstance(data["sections"], list)
        assert len(data["sections"]) > 0


def test_get_policy_by_document_id():
    """GET /api/policies/{document_id} resolves and returns document content."""
    with TestClient(app) as client:
        res = client.get("/api/policies/HOME_LOAN_POLICY")
        assert res.status_code == 200
        data = res.json()
        assert data["filename"] == "01_home_loan_policy.md"
        assert "Home Loan" in data["title"]
        assert len(data["content"]) > 100


def test_get_policy_not_found():
    """GET /api/policies/{filename} returns 404 for nonexistent document."""
    with TestClient(app) as client:
        res = client.get("/api/policies/non_existent_policy.md")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


def test_chat_response_includes_thought_process_and_timing():
    """POST /api/chat returns thought_process and execution_time_ms in response."""
    with TestClient(app) as client:
        # Create session
        conv_res = client.post("/api/conversations", json={"customer_id": "CUST001"})
        assert conv_res.status_code == 201
        conv_id = conv_res.json()["conversation_id"]

        # Send chat message
        chat_res = client.post(
            "/api/chat",
            json={
                "conversation_id": conv_id,
                "customer_id": "CUST001",
                "message": "What is my account balance?",
            },
        )
        assert chat_res.status_code == 200
        chat_data = chat_res.json()

        assert "message" in chat_data
        assert "thought_process" in chat_data
        assert isinstance(chat_data["thought_process"], list)
        assert len(chat_data["thought_process"]) >= 4

        # Check structure of thought steps
        step_nodes = [s.get("node") for s in chat_data["thought_process"]]
        assert "analyze_query" in step_nodes
        assert "route_query" in step_nodes
        assert "validate_context" in step_nodes
        assert "generate_response" in step_nodes

        # Check execution timing
        assert "execution_time_ms" in chat_data
        assert isinstance(chat_data["execution_time_ms"], (int, float))
        assert chat_data["execution_time_ms"] > 0

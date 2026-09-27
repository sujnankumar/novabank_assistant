"""
Test Conversation API Endpoints
===============================
Tests for:
  - POST /api/conversations
  - GET  /api/conversations/{conversation_id}
Phase 8 Implementation.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_conversation_memory, get_memory_orchestrator
from app.main import app
from app.memory.memory_orchestrator import MemoryOrchestrator
from app.memory.sqlite_memory import SQLiteConversationMemory


@pytest.fixture
def isolated_memory(tmp_path: Path):
    """Provides a fresh, isolated temporary SQLite memory for tests."""
    db_file = tmp_path / "conv_api_test.db"
    mem = SQLiteConversationMemory(db_path=db_file)

    app.dependency_overrides[get_conversation_memory] = lambda: mem
    app.dependency_overrides[get_memory_orchestrator] = lambda: MemoryOrchestrator(memory=mem)
    yield mem
    app.dependency_overrides.clear()


@pytest.fixture
def client(isolated_memory):
    """Test client using isolated memory dependency."""
    with TestClient(app) as test_client:
        yield test_client


def test_create_conversation_success(client: TestClient):
    """Creating a conversation succeeds and returns 201 with metadata."""
    payload = {"customer_id": "CUST001"}
    response = client.post("/api/conversations", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert "conversation_id" in data
    assert data["conversation_id"].startswith("conv_")
    assert data["customer_id"] == "CUST001"
    assert "created_at" in data
    assert "updated_at" in data


def test_create_conversation_generates_unique_ids(client: TestClient):
    """Successive conversation creations generate unique conversation IDs."""
    res1 = client.post("/api/conversations", json={"customer_id": "CUST001"})
    res2 = client.post("/api/conversations", json={"customer_id": "CUST001"})

    assert res1.status_code == 201
    assert res2.status_code == 201

    id1 = res1.json()["conversation_id"]
    id2 = res2.json()["conversation_id"]
    assert id1 != id2


def test_get_conversation_history_empty(client: TestClient):
    """Retrieving history for a newly created conversation returns an empty message list."""
    res_create = client.post("/api/conversations", json={"customer_id": "CUST001"})
    conv_id = res_create.json()["conversation_id"]

    res_history = client.get(f"/api/conversations/{conv_id}?customer_id=CUST001")
    assert res_history.status_code == 200

    data = res_history.json()
    assert data["conversation_id"] == conv_id
    assert data["customer_id"] == "CUST001"
    assert data["messages"] == []


def test_get_conversation_history_chronological(client: TestClient, isolated_memory: SQLiteConversationMemory):
    """History returns messages in chronological order with sequence numbers."""
    conv = isolated_memory.create_conversation("CUST001")
    isolated_memory.add_message(conv.conversation_id, "CUST001", "user", "What is my balance?")
    isolated_memory.add_message(conv.conversation_id, "CUST001", "assistant", "Your balance is INR 192,203.99.")
    isolated_memory.add_message(conv.conversation_id, "CUST001", "user", "What about transactions?")
    isolated_memory.add_message(conv.conversation_id, "CUST001", "assistant", "Here are your transactions.")

    res = client.get(f"/api/conversations/{conv.conversation_id}?customer_id=CUST001")
    assert res.status_code == 200
    data = res.json()

    assert data["conversation_id"] == conv.conversation_id
    assert len(data["messages"]) == 4

    seqs = [m["sequence_number"] for m in data["messages"]]
    assert seqs == [1, 2, 3, 4]

    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "What is my balance?"
    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][2]["role"] == "user"
    assert data["messages"][3]["role"] == "assistant"


def test_get_conversation_history_with_limit(client: TestClient, isolated_memory: SQLiteConversationMemory):
    """History limit returns the latest N messages in chronological order."""
    conv = isolated_memory.create_conversation("CUST001")
    for i in range(1, 6):
        isolated_memory.add_message(conv.conversation_id, "CUST001", "user", f"Question {i}")

    res = client.get(f"/api/conversations/{conv.conversation_id}?customer_id=CUST001&limit=2")
    assert res.status_code == 200
    data = res.json()

    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Question 4"
    assert data["messages"][1]["content"] == "Question 5"


def test_get_conversation_history_customer_isolation(client: TestClient, isolated_memory: SQLiteConversationMemory):
    """A customer cannot retrieve another customer's conversation history."""
    conv = isolated_memory.create_conversation("CUST001")
    isolated_memory.add_message(conv.conversation_id, "CUST001", "user", "Private question.")

    # CUST002 attempts to retrieve CUST001's conversation
    res = client.get(f"/api/conversations/{conv.conversation_id}?customer_id=CUST002")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_get_conversation_history_unknown_conversation(client: TestClient):
    """Retrieving an unknown conversation returns 404 with structured error."""
    res = client.get("/api/conversations/conv_unknown?customer_id=CUST001")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "CONVERSATION_NOT_FOUND"
    assert data["error"]["message"] == "Conversation not found."


def test_openapi_schema_includes_phase8_endpoints(client: TestClient):
    """FastAPI OpenAPI schema publishes all Phase 8 routes."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]

    assert "/api/conversations" in paths
    assert "/api/conversations/{conversation_id}" in paths
    assert "/api/chat" in paths
    assert "/api/health" in paths


def test_list_customer_conversations_isolation_and_titles(
    client: TestClient, isolated_memory: SQLiteConversationMemory
):
    """List conversations returns only conversations for the requested customer with titles."""
    # Create conversations for CUST001
    conv1 = isolated_memory.create_conversation("CUST001")
    isolated_memory.add_message(conv1.conversation_id, "CUST001", "user", "What is my credit card limit?")
    isolated_memory.add_message(conv1.conversation_id, "CUST001", "assistant", "Your limit is 50,000 INR.")

    conv2 = isolated_memory.create_conversation("CUST001")
    isolated_memory.add_message(conv2.conversation_id, "CUST001", "user", "How can I apply for a home loan?")

    # Create conversation for CUST002
    conv3 = isolated_memory.create_conversation("CUST002")
    isolated_memory.add_message(conv3.conversation_id, "CUST002", "user", "Secret query for Priya.")

    # 1. Query CUST001
    res1 = client.get("/api/conversations?customer_id=CUST001")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["customer_id"] == "CUST001"
    assert len(data1["conversations"]) == 2

    # Verify conversation IDs and titles
    conv_ids1 = [c["conversation_id"] for c in data1["conversations"]]
    assert conv1.conversation_id in conv_ids1
    assert conv2.conversation_id in conv_ids1
    assert conv3.conversation_id not in conv_ids1  # Absolute customer isolation!

    # Verify title extracted from first user message
    c1_summary = next(c for c in data1["conversations"] if c["conversation_id"] == conv1.conversation_id)
    assert "credit card limit" in c1_summary["title"].lower()
    assert c1_summary["message_count"] == 2

    c2_summary = next(c for c in data1["conversations"] if c["conversation_id"] == conv2.conversation_id)
    assert "home loan" in c2_summary["title"].lower()
    assert c2_summary["message_count"] == 1

    # 2. Query CUST002
    res2 = client.get("/api/conversations?customer_id=CUST002")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["conversations"]) == 1
    assert data2["conversations"][0]["conversation_id"] == conv3.conversation_id
    assert "Secret query" in data2["conversations"][0]["title"]


def test_delete_conversation_success_and_isolation(
    client: TestClient, isolated_memory: SQLiteConversationMemory
):
    """Deleting a conversation removes it and prevents cross-customer deletion."""
    conv = isolated_memory.create_conversation("CUST001")
    isolated_memory.add_message(conv.conversation_id, "CUST001", "user", "Delete me later.")

    # Another customer cannot delete CUST001's conversation
    res_unauth = client.delete(f"/api/conversations/{conv.conversation_id}?customer_id=CUST002")
    assert res_unauth.status_code == 404

    # Owner can delete their conversation
    res_del = client.delete(f"/api/conversations/{conv.conversation_id}?customer_id=CUST001")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "ok"

    # Verifying it's gone from list
    res_list = client.get("/api/conversations?customer_id=CUST001")
    assert res_list.status_code == 200
    assert len(res_list.json()["conversations"]) == 0


def test_empty_conversations_not_saved_or_listed(
    client: TestClient, isolated_memory: SQLiteConversationMemory
):
    """Empty conversations with 0 messages are pruned and never returned in conversation history."""
    # Create empty conversation for CUST001
    conv_empty = isolated_memory.create_conversation("CUST001")

    # Create active conversation with message for CUST001
    conv_active = isolated_memory.create_conversation("CUST001")
    isolated_memory.add_message(conv_active.conversation_id, "CUST001", "user", "Hello assistant")

    # List conversations for CUST001
    res = client.get("/api/conversations?customer_id=CUST001")
    assert res.status_code == 200
    data = res.json()

    # The empty conversation must NOT be in the history list!
    returned_ids = [c["conversation_id"] for c in data["conversations"]]
    assert conv_empty.conversation_id not in returned_ids
    assert conv_active.conversation_id in returned_ids
    assert len(data["conversations"]) == 1

    # Verify that the empty conversation was pruned from SQLite storage
    pruned_conv = isolated_memory.get_conversation(conv_empty.conversation_id, "CUST001")
    assert pruned_conv is None


def test_get_conversation_history_preserves_sources_and_thought_process(
    client: TestClient, isolated_memory: SQLiteConversationMemory
):
    """Verifies that thinking accordion and citation sources persist and are returned on reload."""
    conv = isolated_memory.create_conversation("CUST001")
    isolated_memory.add_message(conv.conversation_id, "CUST001", "user", "What is the home loan interest rate?")

    sources_data = [
        {
            "type": "rag",
            "source": "01_home_loans.md",
            "title": "Home Loan Policy",
            "section": "3. Interest Rates",
            "snippet": "Home loan interest rates start from 8.50% p.a.",
        }
    ]
    thought_data = [
        {"type": "analysis", "title": "Analyze Request", "description": "User asking about home loan rates."},
        {"type": "rag", "title": "Knowledge Base Search", "description": "Found 1 matching policy chunks in 01_home_loans.md"},
        {"type": "generation", "title": "Response Synthesis", "description": "Grounded response generated."},
    ]
    exec_time = 1420.5

    isolated_memory.add_message(
        conv.conversation_id,
        "CUST001",
        "assistant",
        "The interest rate for home loans starts at 8.50% p.a.",
        sources=sources_data,
        thought_process=thought_data,
        execution_time_ms=exec_time,
    )

    res = client.get(f"/api/conversations/{conv.conversation_id}?customer_id=CUST001")
    assert res.status_code == 200
    data = res.json()

    messages = data["messages"]
    assert len(messages) == 2

    user_msg = messages[0]
    assert user_msg["role"] == "user"
    assert user_msg["sources"] is None
    assert user_msg["thought_process"] is None
    assert user_msg["execution_time_ms"] is None

    asst_msg = messages[1]
    assert asst_msg["role"] == "assistant"
    assert asst_msg["sources"] == sources_data
    assert asst_msg["thought_process"] == thought_data
    assert asst_msg["execution_time_ms"] == exec_time


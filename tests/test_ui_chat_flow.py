"""
Test UI Chat Flow and End-to-End Browser Workflows
==================================================
Simulates complete browser-facing client interactions:
  - Initial page load
  - Session creation
  - Single-turn and multi-turn conversations
  - Banking tool invocation via chat
  - RAG policy retrieval via chat
  - Contextual follow-up resolution
  - History restoration
Phase 9 Implementation.
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
    db_file = tmp_path / "ui_flow_test.db"
    mem = SQLiteConversationMemory(db_path=db_file)

    app.dependency_overrides[get_conversation_memory] = lambda: mem
    app.dependency_overrides[get_memory_orchestrator] = lambda: MemoryOrchestrator(memory=mem)
    yield mem
    app.dependency_overrides.clear()


@pytest.fixture
def client(isolated_memory):
    """TestClient wired with isolated memory dependency."""
    with TestClient(app) as test_client:
        yield test_client


def test_complete_ui_chat_lifecycle(client: TestClient):
    """
    Simulates complete user flow:
    1. Browser loads UI (GET /).
    2. Client checks health (GET /api/health).
    3. Client creates new conversation (POST /api/conversations).
    4. Client sends a balance query (POST /api/chat).
    5. Client retrieves history (GET /api/conversations/{id}).
    """
    # 1. Load UI page
    page_res = client.get("/")
    assert page_res.status_code == 200
    assert "NovaBank AI" in page_res.text

    # 2. Check health
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json() == {"status": "ok"}

    # 3. Create conversation for CUST001
    conv_res = client.post("/api/conversations", json={"customer_id": "CUST001"})
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["conversation_id"]
    assert conv_id.startswith("conv_")

    # 4. Send chat message
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
    assert chat_data["conversation_id"] == conv_id
    assert chat_data["customer_id"] == "CUST001"
    assert chat_data["route"] == "TOOL"
    assert "192,203.99" in chat_data["message"]

    # 5. History retrieval
    hist_res = client.get(f"/api/conversations/{conv_id}?customer_id=CUST001")
    assert hist_res.status_code == 200
    messages = hist_res.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is my account balance?"
    assert messages[1]["role"] == "assistant"
    assert "192,203.99" in messages[1]["content"]


def test_ui_multi_turn_follow_up(client: TestClient):
    """
    Simulates a multi-turn conversation:
    Turn 1: "Tell me about home loans." (RAG policy)
    Turn 2: "What are the eligibility requirements?" (Follow-up resolved by memory)
    Verifies that the same conversation ID is used and context is preserved.
    """
    # Create conversation
    conv_res = client.post("/api/conversations", json={"customer_id": "CUST001"})
    conv_id = conv_res.json()["conversation_id"]

    # Turn 1: Discuss home loans
    res1 = client.post(
        "/api/chat",
        json={
            "conversation_id": conv_id,
            "customer_id": "CUST001",
            "message": "Tell me about home loans.",
        },
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["route"] == "RAG"
    assert "home loan" in data1["message"].lower()

    # Turn 2: Follow-up question relying on memory context
    res2 = client.post(
        "/api/chat",
        json={
            "conversation_id": conv_id,
            "customer_id": "CUST001",
            "message": "What are the eligibility requirements?",
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["route"] == "RAG"
    assert "eligib" in data2["message"].lower() or "age" in data2["message"].lower()

    # Verify complete 4-turn history in SQLite
    hist_res = client.get(f"/api/conversations/{conv_id}?customer_id=CUST001")
    assert hist_res.status_code == 200
    history = hist_res.json()["messages"]
    assert len(history) == 4
    assert history[0]["content"] == "Tell me about home loans."
    assert history[2]["content"] == "What are the eligibility requirements?"


def test_ui_banking_tool_query(client: TestClient):
    """
    Simulates banking question: 'What is my balance?'
    Verifies that the request flows through the API to Banking Tools.
    """
    conv_res = client.post("/api/conversations", json={"customer_id": "CUST001"})
    conv_id = conv_res.json()["conversation_id"]

    chat_res = client.post(
        "/api/chat",
        json={
            "conversation_id": conv_id,
            "customer_id": "CUST001",
            "message": "What is my balance?",
        },
    )
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert data["route"] == "TOOL"
    assert "192,203.99" in data["message"]
    assert any(s.get("type") == "tool" for s in data.get("sources", []))

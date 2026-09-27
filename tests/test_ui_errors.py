"""
Test UI Error Handling and Boundary Conditions
==============================================
Tests that the UI-consumed endpoints return structured, safe error representations:
  - Missing or empty customer ID (422)
  - Missing conversation (404)
  - Customer ownership mismatch (404)
  - Empty or whitespace message (422)
  - Memory or internal server failures (500)
  - Traceback masking and absence of sensitive paths
Phase 9 Implementation.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_conversation_memory, get_memory_orchestrator
from app.main import app
from app.memory.exceptions import MemoryStorageError
from app.memory.memory_orchestrator import MemoryOrchestrator
from app.memory.sqlite_memory import SQLiteConversationMemory


@pytest.fixture
def isolated_memory(tmp_path: Path):
    """Provides a fresh, isolated temporary SQLite memory for tests."""
    db_file = tmp_path / "ui_errors_test.db"
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


def test_ui_error_missing_conversation_returns_404(client: TestClient):
    """Attempting chat on an unknown conversation returns 404 with structured error."""
    res = client.post(
        "/api/chat",
        json={
            "conversation_id": "conv_missing_123",
            "customer_id": "CUST001",
            "message": "Hello",
        },
    )
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "CONVERSATION_NOT_FOUND"
    assert "Conversation not found." in data["error"]["message"]


def test_ui_error_customer_mismatch_returns_404(client: TestClient, isolated_memory: SQLiteConversationMemory):
    """Attempting chat with a mismatched customer ID returns 404 without leaking data."""
    conv = isolated_memory.create_conversation("CUST001")

    res = client.post(
        "/api/chat",
        json={
            "conversation_id": conv.conversation_id,
            "customer_id": "CUST002",
            "message": "What is my balance?",
        },
    )
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_ui_error_empty_message_returns_422(client: TestClient, isolated_memory: SQLiteConversationMemory):
    """Submitting empty or whitespace message returns 422."""
    conv = isolated_memory.create_conversation("CUST001")

    res1 = client.post(
        "/api/chat",
        json={
            "conversation_id": conv.conversation_id,
            "customer_id": "CUST001",
            "message": "",
        },
    )
    assert res1.status_code == 422

    res2 = client.post(
        "/api/chat",
        json={
            "conversation_id": conv.conversation_id,
            "customer_id": "CUST001",
            "message": "   \n\t ",
        },
    )
    assert res2.status_code == 422


def test_ui_error_internal_failure_masks_traceback():
    """Server internal errors return safe 500 without leaking stack traces or file paths."""
    mock_orch = MagicMock()
    mock_orch.run_conversation.side_effect = RuntimeError("Fatal DB Crash in C:/Users/secret/path.py")

    app.dependency_overrides[get_memory_orchestrator] = lambda: mock_orch

    with TestClient(app) as test_client:
        res = test_client.post(
            "/api/chat",
            json={
                "conversation_id": "conv_1",
                "customer_id": "CUST001",
                "message": "test",
            },
        )
        assert res.status_code == 500
        data = res.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "path.py" not in data["error"]["message"]
        assert "Traceback" not in res.text

    app.dependency_overrides.clear()


def test_ui_error_storage_failure_masks_sqlite_details():
    """Storage exceptions return safe 500 without leaking sqlite3 errors."""
    mock_orch = MagicMock()
    mock_orch.run_conversation.side_effect = MemoryStorageError("sqlite3.OperationalError: disk full")

    app.dependency_overrides[get_memory_orchestrator] = lambda: mock_orch

    with TestClient(app) as test_client:
        res = test_client.post(
            "/api/chat",
            json={
                "conversation_id": "conv_1",
                "customer_id": "CUST001",
                "message": "test",
            },
        )
        assert res.status_code == 500
        data = res.json()
        assert data["error"]["code"] == "STORAGE_ERROR"
        assert "sqlite3" not in data["error"]["message"].lower()

    app.dependency_overrides.clear()

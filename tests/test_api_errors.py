"""
Test API Error Handling and Validation
======================================
Tests for:
  - Request validation errors (HTTP 422)
  - Boundary conditions and invalid query parameters
  - Memory exception mappings (404, 422, 500)
  - Safe error masking without leaking internal stack traces
  - FastAPI dependency override mechanisms
Phase 8 Implementation.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_conversation_memory, get_memory_orchestrator
from app.main import app
from app.memory.exceptions import (
    ConversationNotFoundError,
    CustomerMismatchError,
    InvalidMessageError,
    MemoryStorageError,
)
from app.memory.memory_orchestrator import MemoryOrchestrator
from app.memory.sqlite_memory import SQLiteConversationMemory


@pytest.fixture
def isolated_memory(tmp_path: Path):
    """Provides a fresh, isolated temporary SQLite memory for tests."""
    db_file = tmp_path / "errors_api_test.db"
    mem = SQLiteConversationMemory(db_path=db_file)

    app.dependency_overrides[get_conversation_memory] = lambda: mem
    app.dependency_overrides[get_memory_orchestrator] = lambda: MemoryOrchestrator(memory=mem)
    yield mem
    app.dependency_overrides.clear()


@pytest.fixture
def client(isolated_memory):
    """Test client with isolated memory dependency."""
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Validation Error Tests (HTTP 422)
# ---------------------------------------------------------------------------

def test_create_conversation_missing_customer_id(client: TestClient):
    """Missing customer_id returns HTTP 422."""
    response = client.post("/api/conversations", json={})
    assert response.status_code == 422


def test_create_conversation_empty_customer_id(client: TestClient):
    """Empty or whitespace-only customer_id returns HTTP 422."""
    res1 = client.post("/api/conversations", json={"customer_id": ""})
    assert res1.status_code == 422

    res2 = client.post("/api/conversations", json={"customer_id": "   "})
    assert res2.status_code == 422


def test_chat_missing_required_fields(client: TestClient):
    """Missing any required chat field returns HTTP 422."""
    res1 = client.post("/api/chat", json={"customer_id": "CUST001", "message": "Hi"})
    assert res1.status_code == 422

    res2 = client.post("/api/chat", json={"conversation_id": "conv_1", "message": "Hi"})
    assert res2.status_code == 422

    res3 = client.post("/api/chat", json={"conversation_id": "conv_1", "customer_id": "CUST001"})
    assert res3.status_code == 422


def test_chat_empty_or_whitespace_fields(client: TestClient):
    """Empty or whitespace-only fields in chat request return HTTP 422."""
    # Empty conversation_id
    res1 = client.post("/api/chat", json={"conversation_id": "   ", "customer_id": "CUST001", "message": "Hi"})
    assert res1.status_code == 422

    # Empty customer_id
    res2 = client.post("/api/chat", json={"conversation_id": "conv_1", "customer_id": "", "message": "Hi"})
    assert res2.status_code == 422

    # Empty message
    res3 = client.post("/api/chat", json={"conversation_id": "conv_1", "customer_id": "CUST001", "message": ""})
    assert res3.status_code == 422

    # Whitespace message
    res4 = client.post("/api/chat", json={"conversation_id": "conv_1", "customer_id": "CUST001", "message": " \t\n "})
    assert res4.status_code == 422


def test_history_missing_or_empty_customer_id(client: TestClient):
    """Missing or empty customer_id query parameter returns HTTP 422."""
    res1 = client.get("/api/conversations/conv_1")
    assert res1.status_code == 422

    res2 = client.get("/api/conversations/conv_1?customer_id=")
    assert res2.status_code == 422

    res3 = client.get("/api/conversations/conv_1?customer_id=   ")
    assert res3.status_code == 422


def test_history_invalid_limit_bounds(client: TestClient, isolated_memory: SQLiteConversationMemory):
    """Limit parameter must satisfy 1 <= limit <= MAX_HISTORY_MESSAGES."""
    conv = isolated_memory.create_conversation("CUST001")

    # Limit = 0 (below min 1)
    res1 = client.get(f"/api/conversations/{conv.conversation_id}?customer_id=CUST001&limit=0")
    assert res1.status_code == 422

    # Limit = -1 (negative)
    res2 = client.get(f"/api/conversations/{conv.conversation_id}?customer_id=CUST001&limit=-1")
    assert res2.status_code == 422

    # Limit = 999 (exceeds default MAX_HISTORY_MESSAGES=20)
    res3 = client.get(f"/api/conversations/{conv.conversation_id}?customer_id=CUST001&limit=999")
    assert res3.status_code == 422


# ---------------------------------------------------------------------------
# Exception Mapping & Error Masking Tests
# ---------------------------------------------------------------------------

def test_conversation_not_found_error_mapped_to_404():
    """ConversationNotFoundError maps to HTTP 404 with structured JSON."""
    mock_memory = MagicMock()
    mock_memory.get_history.side_effect = ConversationNotFoundError("Missing conversation")

    app.dependency_overrides[get_conversation_memory] = lambda: mock_memory

    with TestClient(app) as test_client:
        res = test_client.get("/api/conversations/conv_999?customer_id=CUST001")
        assert res.status_code == 404
        assert res.json() == {
            "error": {
                "code": "CONVERSATION_NOT_FOUND",
                "message": "Conversation not found.",
            }
        }

    app.dependency_overrides.clear()


def test_customer_mismatch_error_mapped_to_404():
    """CustomerMismatchError maps to HTTP 404 to avoid revealing ownership."""
    mock_memory = MagicMock()
    mock_memory.get_history.side_effect = CustomerMismatchError("Access denied")

    app.dependency_overrides[get_conversation_memory] = lambda: mock_memory

    with TestClient(app) as test_client:
        res = test_client.get("/api/conversations/conv_123?customer_id=CUST002")
        assert res.status_code == 404
        assert res.json() == {
            "error": {
                "code": "CONVERSATION_NOT_FOUND",
                "message": "Conversation not found.",
            }
        }

    app.dependency_overrides.clear()


def test_invalid_message_error_mapped_to_422():
    """InvalidMessageError maps to HTTP 422 with structured JSON."""
    mock_orch = MagicMock()
    mock_orch.run_conversation.side_effect = InvalidMessageError("Empty or malformed text")

    app.dependency_overrides[get_memory_orchestrator] = lambda: mock_orch

    with TestClient(app) as test_client:
        res = test_client.post(
            "/api/chat",
            json={"conversation_id": "conv_1", "customer_id": "CUST001", "message": "test"},
        )
        assert res.status_code == 422
        data = res.json()
        assert data["error"]["code"] == "INVALID_MESSAGE"
        assert "Empty or malformed text" in data["error"]["message"]

    app.dependency_overrides.clear()


def test_memory_storage_error_mapped_to_500():
    """MemoryStorageError maps to HTTP 500 without leaking SQLite internal trace."""
    mock_orch = MagicMock()
    mock_orch.run_conversation.side_effect = MemoryStorageError("sqlite3.OperationalError: disk I/O failure")

    app.dependency_overrides[get_memory_orchestrator] = lambda: mock_orch

    with TestClient(app) as test_client:
        res = test_client.post(
            "/api/chat",
            json={"conversation_id": "conv_1", "customer_id": "CUST001", "message": "test"},
        )
        assert res.status_code == 500
        data = res.json()
        assert data["error"]["code"] == "STORAGE_ERROR"
        assert "sqlite3" not in data["error"]["message"].lower()

    app.dependency_overrides.clear()


def test_unexpected_internal_exception_mapped_to_500():
    """Unexpected exceptions map to safe HTTP 500 without exposing Python traces."""
    mock_orch = MagicMock()
    mock_orch.run_conversation.side_effect = RuntimeError("Fatal Python Crash in /internal/path.py")

    app.dependency_overrides[get_memory_orchestrator] = lambda: mock_orch

    with TestClient(app) as test_client:
        res = test_client.post(
            "/api/chat",
            json={"conversation_id": "conv_1", "customer_id": "CUST001", "message": "test"},
        )
        assert res.status_code == 500
        data = res.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "Fatal Python Crash" not in data["error"]["message"]

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Dependency Override Capability Test
# ---------------------------------------------------------------------------

def test_custom_dependency_override_mock():
    """Demonstrates that API dependencies can be cleanly mocked for isolated testing."""
    mock_memory = MagicMock()
    mock_memory.create_conversation.return_value = MagicMock(
        conversation_id="conv_mock_123",
        customer_id="CUST_MOCK",
        created_at="2026-09-25T10:00:00Z",
        updated_at="2026-09-25T10:00:00Z",
    )

    app.dependency_overrides[get_conversation_memory] = lambda: mock_memory

    with TestClient(app) as test_client:
        res = test_client.post("/api/conversations", json={"customer_id": "CUST_MOCK"})
        assert res.status_code == 201
        assert res.json()["conversation_id"] == "conv_mock_123"
        assert res.json()["customer_id"] == "CUST_MOCK"

    app.dependency_overrides.clear()

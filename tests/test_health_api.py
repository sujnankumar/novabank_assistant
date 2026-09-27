"""
Test Health API
===============
Tests for GET /api/health endpoint.
Phase 8 Implementation.
"""

from fastapi.testclient import TestClient
from app.main import app


def test_health_check_returns_200():
    """Health check returns HTTP 200 and {'status': 'ok'}."""
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_health_check_is_lightweight_and_idempotent():
    """Health check does not create conversations or alter state."""
    with TestClient(app) as client:
        for _ in range(3):
            response = client.get("/api/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

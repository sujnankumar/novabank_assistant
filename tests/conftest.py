"""
Pytest Fixtures for NovaBank API Tests
"""

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.json_repository import repository


@pytest.fixture(scope="session")
def client():
    """Create a FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def repo():
    """Access repository directly for ground truth assertions."""
    return repository

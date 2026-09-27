"""
Test API Documentation and OpenAPI Schema
=========================================
Tests for:
  - GET /
  - GET /docs
  - GET /redoc
  - GET /openapi.json
"""

import pytest


def test_root_endpoint(client):
    """Root endpoint returns 200 and NovaBank metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["bank"] == "NovaBank"
    assert data["phase"] == 3
    assert data["status"] == "online"
    assert data["docs"] == "/docs"


def test_docs_page_accessible(client):
    """FastAPI Swagger /docs is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_page_accessible(client):
    """FastAPI ReDoc /redoc is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_json_schema(client):
    """OpenAPI schema contains all 11 required endpoints."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    assert schema["info"]["title"] == "NovaBank Mock Banking API"
    paths = schema["paths"]

    expected_endpoints = [
        "/api/customers/{customer_id}",
        "/api/customers/{customer_id}/profile",
        "/api/accounts/{customer_id}",
        "/api/accounts/{customer_id}/balance",
        "/api/accounts/{customer_id}/transactions",
        "/api/accounts/{customer_id}/transactions/summary",
        "/api/loans",
        "/api/loans/{loan_id}",
        "/api/loans/check-eligibility",
        "/api/products",
        "/api/interest-rates",
    ]

    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Missing endpoint in OpenAPI schema: {endpoint}"

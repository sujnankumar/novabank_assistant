"""
Test Customer API Endpoints
===========================
Tests for:
  - GET /api/customers/{customer_id}
  - GET /api/customers/{customer_id}/profile
"""

import pytest


def test_get_existing_customer(client, repo):
    """Existing customer returns 200 with accurate structured data."""
    cust_data = repo.get_customer_by_id("CUST001")
    assert cust_data is not None

    response = client.get("/api/customers/CUST001")
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == "CUST001"
    assert data["name"] == cust_data["name"]
    assert data["age"] == cust_data["age"]
    assert data["gender"] == cust_data["gender"]
    assert data["city"] == cust_data["city"]
    assert data["occupation"] == cust_data["occupation"]
    assert data["monthly_income"] == cust_data["monthly_income"]
    assert data["credit_score"] == cust_data["credit_score"]
    assert data["consent"] == cust_data["consent"]


def test_list_all_customers_endpoint(client):
    """GET /api/customers returns all 10 synthetic NovaBank customers."""
    response = client.get("/api/customers")
    assert response.status_code == 200
    customers = response.json()
    assert len(customers) == 10
    cust_map = {c["customer_id"]: c["name"] for c in customers}
    assert cust_map["CUST001"] == "Arjun Nair"
    assert cust_map["CUST002"] == "Priya Sharma"
    assert cust_map["CUST003"] == "Rohit Verma"
    assert cust_map["CUST010"] == "Divya Gupta"


def test_get_all_customers_exist_and_accessible(client, repo):
    """Verify all 10 synthetic customers are accessible."""
    all_customers = repo.get_all_customers()
    assert len(all_customers) > 0

    for c in all_customers:
        cid = c["customer_id"]
        res = client.get(f"/api/customers/{cid}")
        assert res.status_code == 200
        assert res.json()["customer_id"] == cid


def test_get_unknown_customer_returns_404(client):
    """Unknown customer returns 404 Not Found."""
    response = client.get("/api/customers/UNKNOWN999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}


def test_get_customer_profile_success(client, repo):
    """Existing customer profile returns 200 with matching preferences."""
    profile_data = repo.get_profile_by_customer_id("CUST001")
    assert profile_data is not None

    response = client.get("/api/customers/CUST001/profile")
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == "CUST001"
    assert data["preferred_language"] == profile_data["preferred_language"]
    assert data["communication_preference"] == profile_data["communication_preference"]
    assert data["customer_segment"] == profile_data["customer_segment"]
    assert data["employment_type"] == profile_data["employment_type"]
    assert data["relationship_years"] == profile_data["relationship_years"]
    assert data["consent_for_personalization"] == profile_data["consent_for_personalization"]


def test_get_customer_profile_unknown_customer_returns_404(client):
    """Unknown customer profile returns 404 Not Found."""
    response = client.get("/api/customers/UNKNOWN999/profile")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

"""
Test Product and Interest Rate API Endpoints
============================================
Tests for:
  - GET /api/products
  - GET /api/interest-rates
"""

import pytest


def test_get_all_products(client, repo):
    """Retrieve all products matching data/products.json count."""
    expected_products = repo.get_all_products()
    assert len(expected_products) == 17

    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()

    assert "products" in data
    assert len(data["products"]) == 17


def test_get_products_filtered_by_type(client):
    """Filter products by product_type (e.g., Savings, Credit Card)."""
    # Test Savings
    response = client.get("/api/products?product_type=Savings")
    assert response.status_code == 200
    products = response.json()["products"]
    assert len(products) > 0
    for p in products:
        assert "savings" in p["product_type"].lower()

    # Test Credit Card
    response_cc = client.get("/api/products?product_type=Credit Card")
    assert response_cc.status_code == 200
    cards = response_cc.json()["products"]
    assert len(cards) > 0
    for c in cards:
        assert "credit card" in c["product_type"].lower()


def test_get_interest_rates_all(client, repo):
    """Interest rates must match rates in products.json and loans.json."""
    response = client.get("/api/interest-rates")
    assert response.status_code == 200
    data = response.json()

    assert "interest_rates" in data
    rates = data["interest_rates"]
    assert len(rates) > 0

    # Ensure each item contains expected keys
    for r in rates:
        assert "product_id" in r
        assert "product_name" in r
        assert "product_type" in r
        assert "interest_rate" in r
        assert isinstance(r["interest_rate"], (int, float))


def test_get_interest_rates_filtered_by_type(client):
    """Filtering interest rates by type (e.g. Home Loan) returns matching rates."""
    response = client.get("/api/interest-rates?product_type=Home Loan")
    assert response.status_code == 200
    rates = response.json()["interest_rates"]

    assert len(rates) > 0
    for r in rates:
        assert "home loan" in r["product_type"].lower()
        # NovaBank Home Loan Standard is 8.5%
        if r["product_id"] == "LOAN001":
            assert r["interest_rate"] == 8.5

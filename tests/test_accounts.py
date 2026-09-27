"""
Test Account and Balance API Endpoints
======================================
Tests for:
  - GET /api/accounts/{customer_id}
  - GET /api/accounts/{customer_id}/balance
"""

import pytest


def test_get_accounts_for_customer(client, repo):
    """Existing customer returns accounts strictly belonging to them."""
    customer_id = "CUST001"
    expected_accounts = repo.get_accounts_by_customer_id(customer_id)
    assert len(expected_accounts) > 0

    response = client.get(f"/api/accounts/{customer_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == customer_id
    assert len(data["accounts"]) == len(expected_accounts)

    for acc in data["accounts"]:
        assert acc["customer_id"] == customer_id
        assert "account_id" in acc
        assert "account_type" in acc
        assert "balance" in acc
        assert "currency" in acc
        assert "status" in acc


def test_get_accounts_unknown_customer_returns_404(client):
    """Unknown customer returns 404."""
    response = client.get("/api/accounts/UNKNOWN999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}


def test_accounts_data_isolation(client, repo):
    """Accounts returned must belong only to the requested customer."""
    all_customers = repo.get_all_customers()
    for cust in all_customers:
        cid = cust["customer_id"]
        res = client.get(f"/api/accounts/{cid}")
        assert res.status_code == 200
        for acc in res.json()["accounts"]:
            assert acc["customer_id"] == cid


def test_get_balance_calculation(client, repo):
    """Balance must match the sum of active accounts directly from structured data."""
    customer_id = "CUST001"
    raw_accounts = repo.get_accounts_by_customer_id(customer_id)

    # Ground truth total from active accounts only
    expected_total = round(
        sum(float(a["balance"]) for a in raw_accounts if a.get("status", "").strip().upper() == "ACTIVE"),
        2
    )

    response = client.get(f"/api/accounts/{customer_id}/balance")
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == customer_id
    assert data["currency"] == "INR"
    assert data["total_balance"] == expected_total
    assert len(data["accounts"]) == len(raw_accounts)


def test_get_balance_all_customers(client, repo):
    """Verify balance calculation across all customers matches active account sums."""
    for c in repo.get_all_customers():
        cid = c["customer_id"]
        raw_accounts = repo.get_accounts_by_customer_id(cid)
        expected_total = round(
            sum(float(a["balance"]) for a in raw_accounts if a.get("status", "").strip().upper() == "ACTIVE"),
            2
        )

        res = client.get(f"/api/accounts/{cid}/balance")
        assert res.status_code == 200
        data = res.json()
        assert data["total_balance"] == expected_total


def test_get_balance_unknown_customer_returns_404(client):
    """Balance for unknown customer returns 404."""
    response = client.get("/api/accounts/UNKNOWN999/balance")
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}

"""
Test Transaction API Endpoints
==============================
Tests for:
  - GET /api/accounts/{customer_id}/transactions
  - GET /api/accounts/{customer_id}/transactions/summary
"""

import pytest


def test_get_transactions_existing_customer(client, repo):
    """Existing customer returns transactions."""
    customer_id = "CUST001"
    response = client.get(f"/api/accounts/{customer_id}/transactions")
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == customer_id
    assert "transactions" in data
    assert "count" in data
    assert data["count"] == len(data["transactions"])


def test_transactions_belong_to_customer_and_accounts(client, repo):
    """Every transaction must satisfy both customer_id and valid customer account_id."""
    customer_id = "CUST001"
    valid_accounts = repo.get_customer_account_ids(customer_id)

    response = client.get(f"/api/accounts/{customer_id}/transactions?limit=100")
    assert response.status_code == 200
    data = response.json()

    for txn in data["transactions"]:
        assert txn["customer_id"] == customer_id
        assert txn["account_id"] in valid_accounts


def test_transactions_ordered_newest_first(client):
    """Default ordering should be newest transaction first."""
    customer_id = "CUST001"
    response = client.get(f"/api/accounts/{customer_id}/transactions?limit=20")
    assert response.status_code == 200
    txns = response.json()["transactions"]

    for i in range(len(txns) - 1):
        assert txns[i]["date"] >= txns[i + 1]["date"]


def test_transactions_limit_and_offset(client):
    """Limit and offset pagination must work properly."""
    customer_id = "CUST001"
    res_all = client.get(f"/api/accounts/{customer_id}/transactions?limit=10")
    assert res_all.status_code == 200
    first_10 = res_all.json()["transactions"]

    res_page = client.get(f"/api/accounts/{customer_id}/transactions?limit=5&offset=5")
    assert res_page.status_code == 200
    next_5 = res_page.json()["transactions"]

    assert len(first_10) == 10
    assert len(next_5) == 5
    assert first_10[5:10] == next_5


def test_transactions_category_filtering(client):
    """Filtering by category returns only transactions in that category."""
    customer_id = "CUST001"
    response = client.get(f"/api/accounts/{customer_id}/transactions?category=Food")
    assert response.status_code == 200
    for txn in response.json()["transactions"]:
        assert txn["category"].lower() == "food"


def test_transactions_type_filtering(client):
    """Filtering by transaction_type (DEBIT/CREDIT) works."""
    customer_id = "CUST001"
    response = client.get(f"/api/accounts/{customer_id}/transactions?transaction_type=DEBIT")
    assert response.status_code == 200
    for txn in response.json()["transactions"]:
        assert txn["type"] == "DEBIT"


def test_transactions_date_filtering(client):
    """Filtering by start_date and end_date works."""
    customer_id = "CUST001"
    start_date = "2026-01-01"
    end_date = "2026-06-30"

    response = client.get(
        f"/api/accounts/{customer_id}/transactions?start_date={start_date}&end_date={end_date}"
    )
    assert response.status_code == 200
    for txn in response.json()["transactions"]:
        assert start_date <= txn["date"] <= end_date


def test_transactions_invalid_date_range_returns_400(client):
    """Invalid date range (start_date > end_date) must return 400 error."""
    customer_id = "CUST001"
    response = client.get(
        f"/api/accounts/{customer_id}/transactions?start_date=2026-06-30&end_date=2026-01-01"
    )
    assert response.status_code == 400
    assert "start_date cannot be after end_date" in response.json()["detail"]


def test_transactions_invalid_date_format_returns_400(client):
    """Malformed date string returns 400 error."""
    customer_id = "CUST001"
    response = client.get(f"/api/accounts/{customer_id}/transactions?start_date=invalid-date")
    assert response.status_code == 400
    assert "Expected YYYY-MM-DD" in response.json()["detail"]


def test_transactions_unknown_customer_returns_404(client):
    """Unknown customer returns 404."""
    response = client.get("/api/accounts/UNKNOWN999/transactions")
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}


# ==================== Transaction Summary Tests ====================


def test_transaction_summary_ground_truth(client, repo):
    """Transaction summary calculations must match the actual dataset totals."""
    customer_id = "CUST001"
    raw_txns = repo.get_transactions_by_customer_id(customer_id)

    expected_credits = round(sum(float(t["amount"]) for t in raw_txns if t["type"] == "CREDIT"), 2)
    expected_debits = round(sum(float(t["amount"]) for t in raw_txns if t["type"] == "DEBIT"), 2)
    expected_count = len(raw_txns)

    response = client.get(f"/api/accounts/{customer_id}/transactions/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == customer_id
    assert data["total_credits"] == expected_credits
    assert data["total_debits"] == expected_debits
    assert data["transaction_count"] == expected_count

    # Verify category spending sums match total debits
    cat_spending = data["category_spending"]
    assert round(sum(cat_spending.values()), 2) == expected_debits


def test_transaction_summary_with_date_range(client, repo):
    """Transaction summary with date range filters correctly."""
    customer_id = "CUST001"
    start_date = "2026-01-01"
    end_date = "2026-03-31"

    raw_txns = repo.get_transactions_by_customer_id(customer_id)
    filtered_txns = [t for t in raw_txns if start_date <= t["date"] <= end_date]

    expected_credits = round(sum(float(t["amount"]) for t in filtered_txns if t["type"] == "CREDIT"), 2)
    expected_debits = round(sum(float(t["amount"]) for t in filtered_txns if t["type"] == "DEBIT"), 2)
    expected_count = len(filtered_txns)

    response = client.get(
        f"/api/accounts/{customer_id}/transactions/summary?start_date={start_date}&end_date={end_date}"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == customer_id
    assert data["period"]["start_date"] == start_date
    assert data["period"]["end_date"] == end_date
    assert data["total_credits"] == expected_credits
    assert data["total_debits"] == expected_debits
    assert data["transaction_count"] == expected_count


def test_transaction_summary_unknown_customer_returns_404(client):
    """Transaction summary for unknown customer returns 404."""
    response = client.get("/api/accounts/UNKNOWN999/transactions/summary")
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}

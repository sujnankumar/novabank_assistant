"""
Test Loan API and Eligibility Endpoints
======================================
Tests for:
  - GET /api/loans
  - GET /api/loans/{loan_id}
  - POST /api/loans/check-eligibility
"""

import pytest


def test_get_all_loans(client, repo):
    """Retrieve all loans matching data/loans.json count."""
    expected_loans = repo.get_all_loans()
    assert len(expected_loans) == 12

    response = client.get("/api/loans")
    assert response.status_code == 200
    data = response.json()

    assert "loans" in data
    assert len(data["loans"]) == 12


def test_get_loans_filtered_by_type(client):
    """Filtering loans by type works properly."""
    response = client.get("/api/loans?loan_type=Home Loan")
    assert response.status_code == 200
    loans = response.json()["loans"]

    assert len(loans) > 0
    for l in loans:
        assert "home loan" in l["loan_type"].lower()


def test_get_loan_by_id_success(client, repo):
    """Existing loan product lookup returns 200 with full details."""
    expected_loan = repo.get_loan_by_id("LOAN001")
    assert expected_loan is not None

    response = client.get("/api/loans/LOAN001")
    assert response.status_code == 200
    data = response.json()

    assert data["loan_id"] == "LOAN001"
    assert data["loan_name"] == expected_loan["loan_name"]
    assert data["interest_rate"] == expected_loan["interest_rate"]
    assert data["minimum_amount"] == expected_loan["minimum_amount"]
    assert data["maximum_amount"] == expected_loan["maximum_amount"]
    assert data["minimum_income"] == expected_loan["minimum_income"]
    assert data["minimum_credit_score"] == expected_loan["minimum_credit_score"]


def test_get_loan_by_id_unknown_returns_404(client):
    """Unknown loan returns 404."""
    response = client.get("/api/loans/LOAN999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Loan not found"}


# ==================== Loan Eligibility Tests ====================


def test_loan_eligibility_eligible_customer(client):
    """
    CUST001 (age 28, income 75000, credit 765) applying for
    LOAN001 (min income 30000, min credit 700, age 21-60, amount 500k-10M)
    with 1,500,000 -> must be eligible with all 4 satisfaction reasons.
    """
    payload = {
        "customer_id": "CUST001",
        "loan_id": "LOAN001",
        "requested_amount": 1500000,
    }
    response = client.post("/api/loans/check-eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == "CUST001"
    assert data["loan_id"] == "LOAN001"
    assert data["eligible"] is True
    assert data["requested_amount"] == 1500000
    assert "Minimum income requirement satisfied" in data["reasons"]
    assert "Minimum credit score requirement satisfied" in data["reasons"]
    assert "Age requirement satisfied" in data["reasons"]
    assert "Requested amount is within the permitted range" in data["reasons"]
    assert "simulated eligibility result" in data["disclaimer"].lower()


def test_loan_eligibility_credit_score_failure(client):
    """
    CUST004 (credit score 690) applying for
    LOAN001 (min credit 700) -> fails credit score check.
    """
    payload = {
        "customer_id": "CUST004",
        "loan_id": "LOAN001",
        "requested_amount": 1000000,
    }
    response = client.post("/api/loans/check-eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["eligible"] is False
    assert any("credit score" in r.lower() for r in data["reasons"])


def test_loan_eligibility_income_failure(client):
    """
    CUST008 (monthly income 18000) applying for
    LOAN001 (min income 30000) -> fails income check.
    """
    payload = {
        "customer_id": "CUST008",
        "loan_id": "LOAN001",
        "requested_amount": 600000,
    }
    response = client.post("/api/loans/check-eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["eligible"] is False
    assert any("monthly income" in r.lower() for r in data["reasons"])


def test_loan_eligibility_age_failure(client):
    """
    CUST009 (age 60) applying for
    LOAN002 (max age 58) -> fails age check.
    """
    payload = {
        "customer_id": "CUST009",
        "loan_id": "LOAN002",
        "requested_amount": 3000000,
    }
    response = client.post("/api/loans/check-eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["eligible"] is False
    assert any("age" in r.lower() for r in data["reasons"])


def test_loan_eligibility_amount_below_minimum(client):
    """Requested amount below minimum amount fails amount check."""
    payload = {
        "customer_id": "CUST001",
        "loan_id": "LOAN001",  # min amount 500,000
        "requested_amount": 100000,
    }
    response = client.post("/api/loans/check-eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["eligible"] is False
    assert any("below the minimum" in r.lower() for r in data["reasons"])


def test_loan_eligibility_amount_above_maximum(client):
    """Requested amount above maximum amount fails amount check."""
    payload = {
        "customer_id": "CUST001",
        "loan_id": "LOAN001",  # max amount 10,000,000
        "requested_amount": 25000000,
    }
    response = client.post("/api/loans/check-eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["eligible"] is False
    assert any("exceeds the maximum" in r.lower() for r in data["reasons"])


def test_loan_eligibility_unknown_customer_returns_404(client):
    """Eligibility check for unknown customer returns 404."""
    payload = {
        "customer_id": "UNKNOWN999",
        "loan_id": "LOAN001",
        "requested_amount": 1000000,
    }
    response = client.post("/api/loans/check-eligibility", json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}


def test_loan_eligibility_unknown_loan_returns_404(client):
    """Eligibility check for unknown loan returns 404."""
    payload = {
        "customer_id": "CUST001",
        "loan_id": "UNKNOWN999",
        "requested_amount": 1000000,
    }
    response = client.post("/api/loans/check-eligibility", json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Loan not found"}

"""
Test Banking Tool Security and Isolation
========================================
Security and isolation verification required by Section 13 and Section 15:
  - CUST001 -> CUST001 data strictly
  - CUST002 -> CUST002 data strictly
  - No cross-customer data leakage
  - Parameter manipulation does not leak other customers' accounts or transactions
  - Tools preserve Phase 3 isolation guarantees
"""

import pytest
from app.tools import (
    get_accounts,
    get_balance,
    get_customer_details,
    get_customer_profile,
    get_transaction_summary,
    get_transactions,
)


def test_customer_details_strict_isolation():
    """Verify customer details returned match strictly the requested customer."""
    cust1 = get_customer_details("CUST001")
    cust2 = get_customer_details("CUST002")

    assert cust1["success"] is True
    assert cust2["success"] is True

    assert cust1["data"]["customer_id"] == "CUST001"
    assert cust2["data"]["customer_id"] == "CUST002"
    assert cust1["data"]["name"] != cust2["data"]["name"]


def test_customer_profile_strict_isolation():
    """Verify profile returned matches strictly the requested customer."""
    prof1 = get_customer_profile("CUST001")
    prof2 = get_customer_profile("CUST002")

    assert prof1["success"] is True
    assert prof2["success"] is True

    assert prof1["data"]["customer_id"] == "CUST001"
    assert prof2["data"]["customer_id"] == "CUST002"


def test_accounts_strict_isolation():
    """Verify account lists returned contain only accounts for requested customer."""
    accs1 = get_accounts("CUST001")
    accs2 = get_accounts("CUST002")

    assert accs1["success"] is True
    assert accs2["success"] is True

    accounts1_ids = {a["account_id"] for a in accs1["data"]["accounts"]}
    accounts2_ids = {a["account_id"] for a in accs2["data"]["accounts"]}

    # No overlapping account IDs between CUST001 and CUST002
    assert len(accounts1_ids.intersection(accounts2_ids)) == 0

    for a in accs1["data"]["accounts"]:
        assert a["customer_id"] == "CUST001"
    for a in accs2["data"]["accounts"]:
        assert a["customer_id"] == "CUST002"


def test_balance_strict_isolation():
    """Verify balance query returns only accounts belonging to that customer."""
    bal1 = get_balance("CUST001")
    bal2 = get_balance("CUST002")

    assert bal1["success"] is True
    assert bal2["success"] is True

    assert bal1["data"]["customer_id"] == "CUST001"
    assert bal2["data"]["customer_id"] == "CUST002"

    bal1_accs = {a["account_id"] for a in bal1["data"]["accounts"]}
    bal2_accs = {a["account_id"] for a in bal2["data"]["accounts"]}
    assert len(bal1_accs.intersection(bal2_accs)) == 0


def test_transactions_strict_isolation():
    """Verify transactions retrieved belong strictly to the requested customer."""
    txns1 = get_transactions("CUST001", limit=100)
    txns2 = get_transactions("CUST002", limit=100)

    assert txns1["success"] is True
    assert txns2["success"] is True

    t1_ids = {t["transaction_id"] for t in txns1["data"]["transactions"]}
    t2_ids = {t["transaction_id"] for t in txns2["data"]["transactions"]}
    assert len(t1_ids.intersection(t2_ids)) == 0

    for t in txns1["data"]["transactions"]:
        assert t["customer_id"] == "CUST001"
    for t in txns2["data"]["transactions"]:
        assert t["customer_id"] == "CUST002"


def test_transaction_summary_isolation():
    """Verify summary calculations are isolated per customer."""
    sum1 = get_transaction_summary("CUST001")
    sum2 = get_transaction_summary("CUST002")

    assert sum1["success"] is True
    assert sum2["success"] is True

    assert sum1["data"]["customer_id"] == "CUST001"
    assert sum2["data"]["customer_id"] == "CUST002"


def test_parameter_manipulation_cannot_leak_data():
    """Attempting SQL injection or path traversal in customer_id does not leak other data."""
    malicious_inputs = [
        "CUST001' OR '1'='1",
        "../CUST002",
        "CUST001; DROP TABLE users;",
        "CUST001/../../CUST002",
    ]

    for bad_id in malicious_inputs:
        res_details = get_customer_details(bad_id)
        assert res_details["success"] is False
        assert res_details["error"]["type"] in ("not_found", "validation_error", "api_error")

        res_accounts = get_accounts(bad_id)
        assert res_accounts["success"] is False
        assert res_accounts["error"]["type"] in ("not_found", "validation_error", "api_error")

        res_txns = get_transactions(bad_id)
        assert res_txns["success"] is False
        assert res_txns["error"]["type"] in ("not_found", "validation_error", "api_error")

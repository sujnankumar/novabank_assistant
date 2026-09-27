"""
NovaBank Banking Tools Verification Script
==========================================
Demonstrates and verifies all 11 banking tools from the app.tools layer.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools import (
    BANKING_TOOLS,
    check_loan_eligibility,
    get_accounts,
    get_all_tool_metadata,
    get_balance,
    get_customer_details,
    get_customer_profile,
    get_interest_rates,
    get_loan_details,
    get_transaction_summary,
    get_transactions,
    list_loans,
    list_products,
)


def verify_tools():
    print("=" * 70)
    print("NOVABANK BANKING TOOLS (PHASE 4) — VERIFICATION")
    print("=" * 70)

    print(f"\nTotal Registered Tools: {len(BANKING_TOOLS)}")

    calls = [
        ("1. get_customer_details", lambda: get_customer_details("CUST001")),
        ("2. get_customer_profile", lambda: get_customer_profile("CUST001")),
        ("3. get_accounts", lambda: get_accounts("CUST001")),
        ("4. get_balance", lambda: get_balance("CUST001")),
        (
            "5. get_transactions",
            lambda: get_transactions("CUST001", limit=2, category="Food"),
        ),
        (
            "6. get_transaction_summary",
            lambda: get_transaction_summary("CUST001", start_date="2026-01-01", end_date="2026-03-31"),
        ),
        ("7. list_loans", lambda: list_loans(loan_type="Home Loan")),
        ("8. get_loan_details", lambda: get_loan_details("LOAN001")),
        (
            "9. check_loan_eligibility",
            lambda: check_loan_eligibility("CUST001", "LOAN001", 1500000),
        ),
        ("10. list_products", lambda: list_products(product_type="Savings")),
        ("11. get_interest_rates", lambda: get_interest_rates(product_type="Home Loan")),
    ]

    for name, call_fn in calls:
        res = call_fn()
        assert res["success"] is True, f"Tool {name} failed: {res}"
        print(f"  [PASS] {name:<30} -> success={res['success']}")

    print("\nMetadata Discovery Check:")
    meta = get_all_tool_metadata()
    assert len(meta) == 11
    print(f"  [PASS] All 11 tool metadata schemas verified.")

    print("\n" + "=" * 70)
    print("ALL 11 BANKING TOOLS VERIFIED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    verify_tools()

"""
NovaBank API Verification Script
================================
Verifies all 11 endpoints and FastAPI documentation endpoints (/docs, /redoc, /openapi.json).
"""

import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def verify():
    print("=" * 70)
    print("NOVABANK MOCK BANKING API — VERIFICATION")
    print("=" * 70)

    # 1. Root and Docs
    print("\n1. Verifying Documentation Endpoints:")
    r = client.get("/docs")
    assert r.status_code == 200
    print(f"  [PASS] GET /docs -> {r.status_code} (Swagger UI active, {len(r.text)} bytes)")

    r = client.get("/redoc")
    assert r.status_code == 200
    print(f"  [PASS] GET /redoc -> {r.status_code} (ReDoc active, {len(r.text)} bytes)")

    r = client.get("/openapi.json")
    assert r.status_code == 200
    openapi = r.json()
    print(f"  [PASS] GET /openapi.json -> {r.status_code} (Title: '{openapi['info']['title']}')")

    print("\n2. Documented Endpoints in OpenAPI Specification:")
    for path, methods in sorted(openapi["paths"].items()):
        for method, spec in methods.items():
            print(f"  {method.upper():5} {path:50} -> {spec.get('summary', '')}")

    # 2. Banking Endpoints Verification
    print("\n3. Testing All Banking Endpoints:")
    tests = [
        ("GET", "/api/customers/CUST001", None),
        ("GET", "/api/customers/CUST001/profile", None),
        ("GET", "/api/accounts/CUST001", None),
        ("GET", "/api/accounts/CUST001/balance", None),
        ("GET", "/api/accounts/CUST001/transactions?limit=2", None),
        ("GET", "/api/accounts/CUST001/transactions/summary", None),
        ("GET", "/api/loans", None),
        ("GET", "/api/loans/LOAN001", None),
        (
            "POST",
            "/api/loans/check-eligibility",
            {"customer_id": "CUST001", "loan_id": "LOAN001", "requested_amount": 1500000},
        ),
        ("GET", "/api/products?product_type=Savings", None),
        ("GET", "/api/interest-rates?product_type=Home Loan", None),
    ]

    for method, path, payload in tests:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json=payload)
        assert res.status_code == 200
        print(f"  [PASS] {method:4} {path:52} -> {res.status_code} OK")

    print("\n" + "=" * 70)
    print("ALL API ENDPOINTS & DOCUMENTATION VERIFIED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    verify()

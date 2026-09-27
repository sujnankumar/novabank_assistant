"""
Test Banking Tools Layer
========================
Tests all 11 Phase 4 banking tools for:
  - Valid structured inputs and outputs
  - Correct API mappings
  - Filtering and pagination
  - Error handling (not found, validation errors, API errors)
  - Tool registry and metadata discovery
  - Mocking strategy and decoupling from external servers
"""

import pytest
from app.tools import (
    BANKING_TOOLS,
    BANKING_TOOLS_DICT,
    check_loan_eligibility,
    get_accounts,
    get_all_tool_metadata,
    get_balance,
    get_customer_details,
    get_customer_profile,
    get_interest_rates,
    get_loan_details,
    get_tool_by_name,
    get_tool_metadata,
    get_transaction_summary,
    get_transactions,
    list_loans,
    list_products,
    reset_api_client,
    set_api_client,
    TOOL_METADATA,
)


@pytest.fixture(autouse=True)
def clean_api_client():
    """Ensure API client is reset after each test."""
    yield
    reset_api_client()


# ==================== Customer Tools ====================


def test_get_customer_details_valid():
    """Retrieve details for valid customer."""
    res = get_customer_details("CUST001")
    assert res["success"] is True
    assert "data" in res
    assert res["data"]["customer_id"] == "CUST001"
    assert "name" in res["data"]
    assert "monthly_income" in res["data"]
    assert "credit_score" in res["data"]


def test_get_customer_details_invalid():
    """Unknown customer returns structured not_found error."""
    res = get_customer_details("UNKNOWN999")
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"
    assert res["error"]["status_code"] == 404


def test_get_customer_details_empty_input():
    """Empty or non-string customer_id returns validation_error."""
    res_empty = get_customer_details("")
    assert res_empty["success"] is False
    assert res_empty["error"]["type"] == "validation_error"

    res_none = get_customer_details(None)
    assert res_none["success"] is False
    assert res_none["error"]["type"] == "validation_error"


def test_get_customer_profile_valid():
    """Retrieve profile for valid customer."""
    res = get_customer_profile("CUST001")
    assert res["success"] is True
    assert res["data"]["customer_id"] == "CUST001"
    assert "preferred_language" in res["data"]
    assert "customer_segment" in res["data"]


def test_get_customer_profile_invalid():
    """Unknown customer profile returns structured not_found error."""
    res = get_customer_profile("UNKNOWN999")
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"
    assert res["error"]["status_code"] == 404


# ==================== Account Tools ====================


def test_get_accounts_valid():
    """Retrieve accounts for valid customer."""
    res = get_accounts("CUST001")
    assert res["success"] is True
    assert res["data"]["customer_id"] == "CUST001"
    assert isinstance(res["data"]["accounts"], list)
    assert len(res["data"]["accounts"]) > 0


def test_get_accounts_invalid():
    """Unknown customer returns structured not_found error."""
    res = get_accounts("UNKNOWN999")
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"
    assert res["error"]["status_code"] == 404


def test_get_balance_valid():
    """Retrieve balance and verify structured output."""
    res = get_balance("CUST001")
    assert res["success"] is True
    assert res["data"]["customer_id"] == "CUST001"
    assert "total_balance" in res["data"]
    assert "accounts" in res["data"]
    assert res["data"]["currency"] == "INR"
    assert isinstance(res["data"]["total_balance"], (int, float))


def test_get_balance_invalid():
    """Unknown customer returns structured not_found error."""
    res = get_balance("UNKNOWN999")
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"
    assert res["error"]["status_code"] == 404


# ==================== Transaction Tools ====================


def test_get_transactions_valid_with_pagination():
    """Retrieve transactions with limit and offset."""
    res = get_transactions("CUST001", limit=5, offset=0)
    assert res["success"] is True
    assert len(res["data"]["transactions"]) == 5
    assert res["data"]["count"] == 5


def test_get_transactions_filtering():
    """Filter transactions by category and type."""
    # Category filter
    res_cat = get_transactions("CUST001", category="Food")
    assert res_cat["success"] is True
    for t in res_cat["data"]["transactions"]:
        assert t["category"].lower() == "food"

    # Type filter
    res_type = get_transactions("CUST001", transaction_type="DEBIT")
    assert res_type["success"] is True
    for t in res_type["data"]["transactions"]:
        assert t["type"] == "DEBIT"


def test_get_transactions_date_filtering():
    """Filter transactions by date range."""
    res = get_transactions(
        "CUST001",
        start_date="2026-01-01",
        end_date="2026-06-30",
    )
    assert res["success"] is True
    for t in res["data"]["transactions"]:
        assert "2026-01-01" <= t["date"] <= "2026-06-30"


def test_get_transactions_invalid_date_range():
    """Invalid date range returns validation_error."""
    res = get_transactions("CUST001", start_date="2026-06-30", end_date="2026-01-01")
    assert res["success"] is False
    assert res["error"]["type"] == "validation_error"


def test_get_transactions_invalid_customer():
    """Unknown customer returns not_found error."""
    res = get_transactions("UNKNOWN999")
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"


def test_get_transaction_summary_valid():
    """Retrieve summary of customer transactions."""
    res = get_transaction_summary("CUST001")
    assert res["success"] is True
    data = res["data"]
    assert data["customer_id"] == "CUST001"
    assert "total_credits" in data
    assert "total_debits" in data
    assert "category_spending" in data
    assert "transaction_count" in data


def test_get_transaction_summary_date_range():
    """Retrieve summary over specific period."""
    res = get_transaction_summary("CUST001", start_date="2026-01-01", end_date="2026-03-31")
    assert res["success"] is True
    assert res["data"]["period"]["start_date"] == "2026-01-01"
    assert res["data"]["period"]["end_date"] == "2026-03-31"


def test_get_transaction_summary_invalid_customer():
    """Unknown customer returns not_found error."""
    res = get_transaction_summary("UNKNOWN999")
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"


# ==================== Loan Tools ====================


def test_list_loans_all():
    """List all available loan products."""
    res = list_loans()
    assert res["success"] is True
    assert "loans" in res["data"]
    assert len(res["data"]["loans"]) == 12


def test_list_loans_filtered():
    """List loans filtered by loan_type."""
    res = list_loans(loan_type="Home Loan")
    assert res["success"] is True
    for l in res["data"]["loans"]:
        assert "home loan" in l["loan_type"].lower()


def test_get_loan_details_valid():
    """Retrieve specific loan product details."""
    res = get_loan_details("LOAN001")
    assert res["success"] is True
    assert res["data"]["loan_id"] == "LOAN001"
    assert "interest_rate" in res["data"]
    assert "minimum_income" in res["data"]


def test_get_loan_details_invalid():
    """Unknown loan returns not_found error."""
    res = get_loan_details("UNKNOWN_LOAN")
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"


def test_check_loan_eligibility_eligible():
    """Eligible customer request returns eligible=True."""
    res = check_loan_eligibility(
        customer_id="CUST001",
        loan_id="LOAN001",
        requested_amount=1500000,
    )
    assert res["success"] is True
    assert res["data"]["eligible"] is True
    assert res["data"]["customer_id"] == "CUST001"
    assert res["data"]["loan_id"] == "LOAN001"
    assert len(res["data"]["reasons"]) == 4
    assert "simulated eligibility result" in res["data"]["disclaimer"].lower()


def test_check_loan_eligibility_ineligible():
    """Ineligible customer request returns eligible=False with specific failure reasons."""
    # CUST004 has credit score 690 < LOAN001 min 700
    res = check_loan_eligibility(
        customer_id="CUST004",
        loan_id="LOAN001",
        requested_amount=1000000,
    )
    assert res["success"] is True
    assert res["data"]["eligible"] is False
    assert any("credit score" in r.lower() for r in res["data"]["reasons"])


def test_check_loan_eligibility_invalid_amount():
    """Requested amount <= 0 returns validation_error."""
    res_zero = check_loan_eligibility("CUST001", "LOAN001", 0)
    assert res_zero["success"] is False
    assert res_zero["error"]["type"] == "validation_error"

    res_neg = check_loan_eligibility("CUST001", "LOAN001", -50000)
    assert res_neg["success"] is False
    assert res_neg["error"]["type"] == "validation_error"


def test_check_loan_eligibility_unknown_customer():
    """Eligibility check with unknown customer returns not_found."""
    res = check_loan_eligibility("UNKNOWN999", "LOAN001", 500000)
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"


def test_check_loan_eligibility_unknown_loan():
    """Eligibility check with unknown loan returns not_found."""
    res = check_loan_eligibility("CUST001", "UNKNOWN_LOAN", 500000)
    assert res["success"] is False
    assert res["error"]["type"] == "not_found"


# ==================== Product Tools ====================


def test_list_products_all():
    """List all available banking products."""
    res = list_products()
    assert res["success"] is True
    assert "products" in res["data"]
    assert len(res["data"]["products"]) == 17


def test_list_products_filtered():
    """List banking products filtered by product_type."""
    res = list_products(product_type="Savings")
    assert res["success"] is True
    for p in res["data"]["products"]:
        assert "savings" in p["product_type"].lower()


def test_get_interest_rates_all():
    """Retrieve all interest rates."""
    res = get_interest_rates()
    assert res["success"] is True
    assert "interest_rates" in res["data"]
    assert len(res["data"]["interest_rates"]) > 0


def test_get_interest_rates_filtered():
    """Retrieve interest rates filtered by type."""
    res = get_interest_rates(product_type="Home Loan")
    assert res["success"] is True
    for r in res["data"]["interest_rates"]:
        assert "home loan" in r["product_type"].lower()


# ==================== Registry & Metadata ====================


def test_banking_tools_registry():
    """Verify all 11 tools are registered in BANKING_TOOLS and BANKING_TOOLS_DICT."""
    assert len(BANKING_TOOLS) == 11
    assert len(BANKING_TOOLS_DICT) == 11

    expected_names = [
        "get_customer_details",
        "get_customer_profile",
        "get_accounts",
        "get_balance",
        "get_transactions",
        "get_transaction_summary",
        "list_loans",
        "get_loan_details",
        "check_loan_eligibility",
        "list_products",
        "get_interest_rates",
    ]

    for name in expected_names:
        assert name in BANKING_TOOLS_DICT
        tool = get_tool_by_name(name)
        assert callable(tool)


def test_tool_metadata():
    """Verify metadata is complete and accurate for all tools."""
    all_meta = get_all_tool_metadata()
    assert len(all_meta) == 11

    for meta in all_meta:
        assert "name" in meta
        assert "description" in meta
        assert "parameters" in meta
        assert "return_structure" in meta

    balance_meta = get_tool_metadata("get_balance")
    assert balance_meta is not None
    assert balance_meta["name"] == "get_balance"
    assert "customer_id" in balance_meta["parameters"]
    assert balance_meta["parameters"]["customer_id"]["required"] is True


# ==================== Mocking Strategy Tests ====================


class MockResponse:
    def __init__(self, status_code: int, data: dict):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class MockHttpClient:
    """Mock HTTP client verifying parameter passing and endpoint mapping."""

    def __init__(self):
        self.last_method = None
        self.last_url = None
        self.last_params = None
        self.last_json = None

    def request(self, method, url, params=None, json=None):
        self.last_method = method
        self.last_url = url
        self.last_params = params
        self.last_json = json
        return MockResponse(200, {"mocked": True, "method": method, "url": url})


def test_mocking_strategy_requests_and_params():
    """Verify tool uses client without needing live network."""
    mock_client = MockHttpClient()
    set_api_client(mock_client)

    res = get_customer_details("CUST999")
    assert res["success"] is True
    assert res["data"]["mocked"] is True
    assert mock_client.last_method == "GET"
    assert mock_client.last_url == "/api/customers/CUST999"


def test_mocking_strategy_error_handling():
    """Verify tool converts HTTP 500 / API error into structured error."""
    class FailingClient:
        def request(self, method, url, params=None, json=None):
            return MockResponse(500, {"detail": "Internal database error"})

    set_api_client(FailingClient())
    res = get_balance("CUST001")
    assert res["success"] is False
    assert res["error"]["type"] == "api_error"
    assert res["error"]["status_code"] == 500
    assert "Internal database error" in res["error"]["message"]


def test_mocking_strategy_network_exception():
    """Verify tool handles network connection failure gracefully."""
    class NetworkErrorClient:
        def request(self, method, url, params=None, json=None):
            raise ConnectionError("Failed to reach server")

    set_api_client(NetworkErrorClient())
    res = list_loans()
    assert res["success"] is False
    assert res["error"]["type"] == "api_error"
    assert "Failed to reach server" in res["error"]["message"]

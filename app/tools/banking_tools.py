"""
NovaBank Banking Tools Implementation
=====================================
Structured, deterministic tool adapter layer over the Phase 3 Banking APIs.
Enforces customer isolation, structured inputs and outputs, and error handling.
Contains NO LLM, agent, RAG, or conversational logic.
"""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from fastapi.testclient import TestClient

DEFAULT_TRANSACTION_LIMIT: int = 5
MAX_TRANSACTION_LIMIT: int = 100


class BankingApiClient:
    """
    HTTP/API client adapter for calling Phase 3 Banking APIs.
    Defaults to in-process FastAPI TestClient without requiring external network ports.
    Supports mocking and client injection for unit tests.
    """

    def __init__(self, client: Optional[Any] = None, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._custom_client = client

    def get_client(self) -> Any:
        if self._custom_client is not None:
            return self._custom_client
        from app.main import app
        return TestClient(app, base_url=self.base_url)

    def set_client(self, client: Optional[Any]) -> None:
        """Inject a custom or mock client."""
        self._custom_client = client

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform request and normalize into structured tool response."""
        client = self.get_client()
        url = endpoint if endpoint.startswith("/") else f"/{endpoint}"

        try:
            # Clean None params
            clean_params = {k: v for k, v in params.items() if v is not None} if params else None

            # Execute HTTP call via client
            if hasattr(client, "request"):
                response = client.request(method, url, params=clean_params, json=json_data)
            else:
                # Fallback for simple mock objects with get/post methods
                call_fn = getattr(client, method.lower())
                if method.upper() == "GET":
                    response = call_fn(url, params=clean_params)
                else:
                    response = call_fn(url, json=json_data)

            status_code = getattr(response, "status_code", 200)

            # Success responses (2xx)
            if 200 <= status_code < 300:
                body = response.json() if callable(getattr(response, "json", None)) else response.json
                return {
                    "success": True,
                    "data": body,
                }

            # Failure responses (4xx, 5xx)
            try:
                err_body = response.json() if callable(getattr(response, "json", None)) else response.json
                if isinstance(err_body, dict):
                    message = err_body.get("detail", str(err_body))
                else:
                    message = str(err_body)
            except Exception:
                message = getattr(response, "text", f"HTTP error {status_code}")

            if status_code == 404:
                error_type = "not_found"
            elif status_code in (400, 422):
                error_type = "validation_error"
            else:
                error_type = "api_error"

            return {
                "success": False,
                "error": {
                    "type": error_type,
                    "message": message,
                    "status_code": status_code,
                },
            }

        except Exception as exc:
            return {
                "success": False,
                "error": {
                    "type": "api_error",
                    "message": f"Banking API error: {str(exc)}",
                    "status_code": 500,
                },
            }


# Default global client instance
_api_client = BankingApiClient()


def get_api_client() -> BankingApiClient:
    """Return the active BankingApiClient."""
    return _api_client


def set_api_client(client: Optional[Any]) -> None:
    """Set custom or mock client on the active BankingApiClient."""
    _api_client.set_client(client)


def reset_api_client() -> None:
    """Reset the BankingApiClient to the default in-process TestClient."""
    _api_client.set_client(None)


# ==================== Input Validation Helpers ====================


def _validate_customer_id(customer_id: Any) -> Optional[Dict[str, Any]]:
    """Validate customer_id is a non-empty string."""
    if customer_id is None or not isinstance(customer_id, str) or not customer_id.strip():
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Invalid customer_id: must be a non-empty string",
                "status_code": 400,
            },
        }
    return None


def _validate_loan_id(loan_id: Any) -> Optional[Dict[str, Any]]:
    """Validate loan_id is a non-empty string."""
    if loan_id is None or not isinstance(loan_id, str) or not loan_id.strip():
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Invalid loan_id: must be a non-empty string",
                "status_code": 400,
            },
        }
    return None


# ==================== Banking Tools ====================


def get_customer_details(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve basic customer information for a NovaBank customer.

    Parameters:
        customer_id (str): Unique customer ID (e.g. 'CUST001')

    Returns:
        dict: Structured tool result with customer demographic details.
    """
    err = _validate_customer_id(customer_id)
    if err:
        return err

    return _api_client.request("GET", f"/api/customers/{customer_id.strip()}")


def get_customer_profile(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve the customer's banking profile, preferences, and personalization flags.

    Parameters:
        customer_id (str): Unique customer ID (e.g. 'CUST001')

    Returns:
        dict: Structured tool result with customer profile details.
    """
    err = _validate_customer_id(customer_id)
    if err:
        return err

    return _api_client.request("GET", f"/api/customers/{customer_id.strip()}/profile")


def get_accounts(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve all accounts belonging to a NovaBank customer.

    Parameters:
        customer_id (str): Unique customer ID (e.g. 'CUST001')

    Returns:
        dict: Structured tool result containing list of accounts.
    """
    err = _validate_customer_id(customer_id)
    if err:
        return err

    return _api_client.request("GET", f"/api/accounts/{customer_id.strip()}")


def get_balance(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve the customer's account balance information and active total balance.

    Parameters:
        customer_id (str): Unique customer ID (e.g. 'CUST001')

    Returns:
        dict: Structured tool result containing account balances and calculated total.
    """
    err = _validate_customer_id(customer_id)
    if err:
        return err

    return _api_client.request("GET", f"/api/accounts/{customer_id.strip()}/balance")


def get_transactions(
    customer_id: str,
    limit: int = DEFAULT_TRANSACTION_LIMIT,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_id: Optional[str] = None,
    sort: str = "desc",
) -> Dict[str, Any]:
    """
    Retrieve paginated customer transaction history with supported filtering.

    Parameters:
        customer_id (str): Unique customer ID (e.g. 'CUST001')
        limit (int): Max transactions to return (default: 5, max: 100)
        offset (int): Pagination offset (default: 0)
        transaction_type (str, optional): Filter by type ('CREDIT' or 'DEBIT')
        category (str, optional): Filter by category (e.g. 'Food', 'Shopping')
        merchant (str, optional): Filter by merchant name
        start_date (str, optional): Transactions on or after YYYY-MM-DD
        end_date (str, optional): Transactions on or before YYYY-MM-DD
        account_id (str, optional): Filter by specific account ID
        sort (str, optional): Sort direction ('desc' or 'asc', default 'desc')

    Returns:
        dict: Structured tool result containing transactions list and count.
    """
    err = _validate_customer_id(customer_id)
    if err:
        return err

    if limit is not None and (not isinstance(limit, int) or limit < 1):
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Invalid limit: must be an integer >= 1",
                "status_code": 400,
            },
        }

    # Enforce server-side safety maximum limit cap
    effective_limit = min(limit, MAX_TRANSACTION_LIMIT) if limit is not None else DEFAULT_TRANSACTION_LIMIT

    if offset is not None and (not isinstance(offset, int) or offset < 0):
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Invalid offset: must be an integer >= 0",
                "status_code": 400,
            },
        }

    if start_date and end_date and start_date > end_date:
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Invalid date range: start_date cannot be after end_date.",
                "status_code": 400,
            },
        }

    params = {
        "limit": effective_limit,
        "offset": offset,
        "transaction_type": transaction_type,
        "category": category,
        "merchant": merchant,
        "start_date": start_date,
        "end_date": end_date,
        "account_id": account_id,
        "sort": sort,
    }

    return _api_client.request(
        "GET",
        f"/api/accounts/{customer_id.strip()}/transactions",
        params=params,
    )


def get_transaction_summary(
    customer_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve financial summary of customer transactions over an optional period.

    Parameters:
        customer_id (str): Unique customer ID (e.g. 'CUST001')
        start_date (str, optional): Period start date (YYYY-MM-DD)
        end_date (str, optional): Period end date (YYYY-MM-DD)

    Returns:
        dict: Structured tool result containing credits, debits, and category spending.
    """
    err = _validate_customer_id(customer_id)
    if err:
        return err

    if start_date and end_date and start_date > end_date:
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Invalid date range: start_date cannot be after end_date.",
                "status_code": 400,
            },
        }

    params = {
        "start_date": start_date,
        "end_date": end_date,
    }

    return _api_client.request(
        "GET",
        f"/api/accounts/{customer_id.strip()}/transactions/summary",
        params=params,
    )


def list_loans(loan_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve available NovaBank loan products with optional type filter.

    Parameters:
        loan_type (str, optional): Filter by loan type (e.g. 'Home Loan')

    Returns:
        dict: Structured tool result with list of loan products.
    """
    params = {"loan_type": loan_type} if loan_type else None
    return _api_client.request("GET", "/api/loans", params=params)


def get_loan_details(loan_id: str) -> Dict[str, Any]:
    """
    Retrieve details and eligibility criteria for a specific loan product.

    Parameters:
        loan_id (str): Unique loan ID (e.g. 'LOAN001')

    Returns:
        dict: Structured tool result with loan product details.
    """
    err = _validate_loan_id(loan_id)
    if err:
        return err

    return _api_client.request("GET", f"/api/loans/{loan_id.strip()}")


def check_loan_eligibility(
    customer_id: str,
    loan_id: str,
    requested_amount: float,
) -> Dict[str, Any]:
    """
    Perform a simulated, deterministic loan eligibility check.

    Parameters:
        customer_id (str): Unique customer ID (e.g. 'CUST001')
        loan_id (str): Unique loan ID (e.g. 'LOAN001')
        requested_amount (float): Desired loan amount in INR

    Returns:
        dict: Structured tool result with eligibility outcome, reasons, and disclaimer.
    """
    err_c = _validate_customer_id(customer_id)
    if err_c:
        return err_c

    err_l = _validate_loan_id(loan_id)
    if err_l:
        return err_l

    if requested_amount is None or not isinstance(requested_amount, (int, float)) or requested_amount <= 0:
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Invalid requested_amount: must be a positive number greater than 0",
                "status_code": 400,
            },
        }

    payload = {
        "customer_id": customer_id.strip(),
        "loan_id": loan_id.strip(),
        "requested_amount": float(requested_amount),
    }

    return _api_client.request("POST", "/api/loans/check-eligibility", json_data=payload)


def list_products(product_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve available NovaBank banking products (accounts, credit cards, FDs).

    Parameters:
        product_type (str, optional): Filter by product type (e.g. 'Savings', 'Credit Card')

    Returns:
        dict: Structured tool result with list of banking products.
    """
    params = {"product_type": product_type} if product_type else None
    return _api_client.request("GET", "/api/products", params=params)


def get_interest_rates(product_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve current simulated NovaBank interest rates across products and loans.

    Parameters:
        product_type (str, optional): Filter by product or loan type (e.g. 'Home Loan')

    Returns:
        dict: Structured tool result containing interest rates.
    """
    params = {"product_type": product_type} if product_type else None
    return _api_client.request("GET", "/api/interest-rates", params=params)


# ==================== Tool Registry ====================

BANKING_TOOLS: List[Callable[..., Dict[str, Any]]] = [
    get_customer_details,
    get_customer_profile,
    get_accounts,
    get_balance,
    get_transactions,
    get_transaction_summary,
    list_loans,
    get_loan_details,
    check_loan_eligibility,
    list_products,
    get_interest_rates,
]

BANKING_TOOLS_DICT: Dict[str, Callable[..., Dict[str, Any]]] = {
    tool.__name__: tool for tool in BANKING_TOOLS
}


def get_tool_by_name(name: str) -> Optional[Callable[..., Dict[str, Any]]]:
    """Look up a banking tool by its function name."""
    return BANKING_TOOLS_DICT.get(name)


# ==================== Tool Metadata ====================

TOOL_METADATA: Dict[str, Dict[str, Any]] = {
    "get_customer_details": {
        "name": "get_customer_details",
        "description": "Retrieve basic demographic and contact information for a NovaBank customer.",
        "parameters": {
            "customer_id": {
                "type": "string",
                "required": True,
                "description": "Unique customer ID (e.g. CUST001)",
            }
        },
        "return_structure": {
            "customer_id": "string",
            "name": "string",
            "age": "integer",
            "gender": "string",
            "city": "string",
            "occupation": "string",
            "monthly_income": "number",
            "credit_score": "integer",
            "consent": "boolean",
        },
    },
    "get_customer_profile": {
        "name": "get_customer_profile",
        "description": "Retrieve the customer's banking profile, preferences, and personalization flags.",
        "parameters": {
            "customer_id": {
                "type": "string",
                "required": True,
                "description": "Unique customer ID (e.g. CUST001)",
            }
        },
        "return_structure": {
            "customer_id": "string",
            "preferred_language": "string",
            "communication_preference": "string",
            "customer_segment": "string",
            "employment_type": "string",
            "relationship_years": "integer",
            "consent_for_personalization": "boolean",
        },
    },
    "get_accounts": {
        "name": "get_accounts",
        "description": "Retrieve all bank accounts belonging to a NovaBank customer.",
        "parameters": {
            "customer_id": {
                "type": "string",
                "required": True,
                "description": "Unique customer ID (e.g. CUST001)",
            }
        },
        "return_structure": {
            "customer_id": "string",
            "accounts": "list of account objects",
        },
    },
    "get_balance": {
        "name": "get_balance",
        "description": "Retrieve customer account balances and calculated total active balance.",
        "parameters": {
            "customer_id": {
                "type": "string",
                "required": True,
                "description": "Unique customer ID (e.g. CUST001)",
            }
        },
        "return_structure": {
            "customer_id": "string",
            "accounts": "list of balance items",
            "total_balance": "number",
            "currency": "string",
        },
    },
    "get_transactions": {
        "name": "get_transactions",
        "description": "Retrieve paginated transaction history for a customer with optional filters.",
        "parameters": {
            "customer_id": {
                "type": "string",
                "required": True,
                "description": "Unique customer ID (e.g. CUST001)",
            },
            "limit": {
                "type": "integer",
                "required": False,
                "description": "Maximum number of transactions to return (default 5, max 100)",
            },
            "offset": {
                "type": "integer",
                "required": False,
                "description": "Pagination offset (default 0)",
            },
            "transaction_type": {
                "type": "string",
                "required": False,
                "description": "Filter by type (CREDIT or DEBIT)",
            },
            "category": {
                "type": "string",
                "required": False,
                "description": "Filter by spending category",
            },
            "merchant": {
                "type": "string",
                "required": False,
                "description": "Filter by merchant name",
            },
            "start_date": {
                "type": "string",
                "required": False,
                "description": "Filter on or after YYYY-MM-DD",
            },
            "end_date": {
                "type": "string",
                "required": False,
                "description": "Filter on or before YYYY-MM-DD",
            },
            "account_id": {
                "type": "string",
                "required": False,
                "description": "Filter by specific account ID",
            },
            "sort": {
                "type": "string",
                "required": False,
                "description": "Sort order ('desc' or 'asc', default: desc)",
            },
        },
        "return_structure": {
            "customer_id": "string",
            "transactions": "list of transaction objects",
            "count": "integer",
        },
    },
    "get_transaction_summary": {
        "name": "get_transaction_summary",
        "description": "Retrieve financial summary of customer transactions over an optional period.",
        "parameters": {
            "customer_id": {
                "type": "string",
                "required": True,
                "description": "Unique customer ID (e.g. CUST001)",
            },
            "start_date": {
                "type": "string",
                "required": False,
                "description": "Start date YYYY-MM-DD",
            },
            "end_date": {
                "type": "string",
                "required": False,
                "description": "End date YYYY-MM-DD",
            },
        },
        "return_structure": {
            "customer_id": "string",
            "period": "object with start_date and end_date",
            "total_credits": "number",
            "total_debits": "number",
            "transaction_count": "integer",
            "category_spending": "object mapping category to amount",
        },
    },
    "list_loans": {
        "name": "list_loans",
        "description": "Retrieve available NovaBank loan products with optional type filter.",
        "parameters": {
            "loan_type": {
                "type": "string",
                "required": False,
                "description": "Filter by loan type (e.g. Home Loan, Personal Loan)",
            }
        },
        "return_structure": {
            "loans": "list of loan product objects",
        },
    },
    "get_loan_details": {
        "name": "get_loan_details",
        "description": "Retrieve details and eligibility criteria for a specific loan product.",
        "parameters": {
            "loan_id": {
                "type": "string",
                "required": True,
                "description": "Unique loan ID (e.g. LOAN001)",
            }
        },
        "return_structure": {
            "loan_id": "string",
            "loan_name": "string",
            "loan_type": "string",
            "minimum_amount": "integer",
            "maximum_amount": "integer",
            "interest_rate": "number",
            "minimum_income": "integer",
            "minimum_credit_score": "integer",
            "minimum_age": "integer",
            "maximum_age": "integer",
            "maximum_tenure_years": "integer",
            "processing_fee_percent": "number",
            "required_documents": "list of strings",
        },
    },
    "check_loan_eligibility": {
        "name": "check_loan_eligibility",
        "description": "Perform a deterministic simulated loan eligibility check for a customer and loan.",
        "parameters": {
            "customer_id": {
                "type": "string",
                "required": True,
                "description": "Unique customer ID (e.g. CUST001)",
            },
            "loan_id": {
                "type": "string",
                "required": True,
                "description": "Unique loan ID (e.g. LOAN001)",
            },
            "requested_amount": {
                "type": "number",
                "required": True,
                "description": "Requested loan amount in INR",
            },
        },
        "return_structure": {
            "eligible": "boolean",
            "customer_id": "string",
            "loan_id": "string",
            "requested_amount": "number",
            "reasons": "list of strings",
            "disclaimer": "string",
        },
    },
    "list_products": {
        "name": "list_products",
        "description": "Retrieve available NovaBank banking products.",
        "parameters": {
            "product_type": {
                "type": "string",
                "required": False,
                "description": "Filter by product type (e.g. Savings, Credit Card)",
            }
        },
        "return_structure": {
            "products": "list of banking product objects",
        },
    },
    "get_interest_rates": {
        "name": "get_interest_rates",
        "description": "Retrieve current simulated NovaBank interest rates.",
        "parameters": {
            "product_type": {
                "type": "string",
                "required": False,
                "description": "Filter by product or loan type",
            }
        },
        "return_structure": {
            "interest_rates": "list of interest rate objects",
        },
    },
}


def get_tool_metadata(name: str) -> Optional[Dict[str, Any]]:
    """Return discovery metadata for a specific tool."""
    return TOOL_METADATA.get(name)


def get_all_tool_metadata() -> List[Dict[str, Any]]:
    """Return discovery metadata for all registered banking tools."""
    return list(TOOL_METADATA.values())

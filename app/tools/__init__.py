"""
NovaBank Banking Tools Package
==============================
Exposes callable banking tools, metadata registry, and schemas.
"""

from .banking_tools import (
    BANKING_TOOLS,
    BANKING_TOOLS_DICT,
    BankingApiClient,
    check_loan_eligibility,
    get_accounts,
    get_all_tool_metadata,
    get_api_client,
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
from .schemas import ToolError, ToolMetadata, ToolResult

__all__ = [
    # Tools
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
    # Registry & Metadata
    "BANKING_TOOLS",
    "BANKING_TOOLS_DICT",
    "get_tool_by_name",
    "TOOL_METADATA",
    "get_tool_metadata",
    "get_all_tool_metadata",
    # Client Management
    "BankingApiClient",
    "get_api_client",
    "set_api_client",
    "reset_api_client",
    # Schemas
    "ToolResult",
    "ToolError",
    "ToolMetadata",
]

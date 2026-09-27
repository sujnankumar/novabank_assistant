"""
NovaBank Banking Tools Schemas
==============================
Pydantic models for structured tool inputs, results, errors, and metadata.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolError(BaseModel):
    """Structured error representation for banking tools."""

    type: str = Field(..., description="Error classification (not_found, validation_error, api_error)")
    message: str = Field(..., description="Human-readable error explanation")
    status_code: Optional[int] = Field(None, description="HTTP status code if originated from API")


class ToolResult(BaseModel):
    """Standardized tool execution result."""

    success: bool = Field(..., description="Whether tool execution succeeded")
    data: Optional[Any] = Field(None, description="Structured data returned on success")
    error: Optional[ToolError] = Field(None, description="Structured error on failure")

    def to_dict(self) -> Dict[str, Any]:
        """Convert ToolResult to a standard dictionary."""
        return self.model_dump(exclude_none=True)


# ==================== Input Parameter Schemas ====================


class CustomerDetailsInput(BaseModel):
    """Input for get_customer_details."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")


class CustomerProfileInput(BaseModel):
    """Input for get_customer_profile."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")


class AccountsInput(BaseModel):
    """Input for get_accounts."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")


class BalanceInput(BaseModel):
    """Input for get_balance."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")


class TransactionsInput(BaseModel):
    """Input for get_transactions."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")
    limit: int = Field(default=50, ge=1, le=100, description="Max transactions to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    transaction_type: Optional[str] = Field(default=None, description="Filter by DEBIT or CREDIT")
    category: Optional[str] = Field(default=None, description="Filter by spending category")
    merchant: Optional[str] = Field(default=None, description="Filter by merchant name")
    start_date: Optional[str] = Field(default=None, description="Filter on or after YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="Filter on or before YYYY-MM-DD")


class TransactionSummaryInput(BaseModel):
    """Input for get_transaction_summary."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")
    start_date: Optional[str] = Field(default=None, description="Start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="End date YYYY-MM-DD")


class ListLoansInput(BaseModel):
    """Input for list_loans."""

    loan_type: Optional[str] = Field(default=None, description="Filter by loan type (e.g. Home Loan)")


class LoanDetailsInput(BaseModel):
    """Input for get_loan_details."""

    loan_id: str = Field(..., description="Unique loan ID (e.g. LOAN001)")


class LoanEligibilityInput(BaseModel):
    """Input for check_loan_eligibility."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")
    loan_id: str = Field(..., description="Unique loan ID (e.g. LOAN001)")
    requested_amount: float = Field(..., gt=0, description="Requested loan amount in INR")


class ListProductsInput(BaseModel):
    """Input for list_products."""

    product_type: Optional[str] = Field(default=None, description="Filter by product type (e.g. Savings)")


class InterestRatesInput(BaseModel):
    """Input for get_interest_rates."""

    product_type: Optional[str] = Field(default=None, description="Filter by product or loan type")


class ToolMetadata(BaseModel):
    """Metadata describing a callable banking tool."""

    name: str
    description: str
    parameters: Dict[str, Any]
    return_structure: Dict[str, Any]

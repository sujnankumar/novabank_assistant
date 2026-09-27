"""
Transaction Pydantic Schemas
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """NovaBank Transaction Model matching data/transactions.json."""

    transaction_id: str = Field(..., description="Unique transaction ID (e.g. TXN00001)")
    customer_id: str = Field(..., description="Customer ID")
    account_id: str = Field(..., description="Account ID associated with transaction")
    date: str = Field(..., description="Date of transaction (YYYY-MM-DD)")
    type: str = Field(..., description="Transaction type (CREDIT or DEBIT)")
    amount: float = Field(..., ge=0, description="Transaction amount in INR")
    merchant: str = Field(..., description="Merchant or entity involved")
    category: str = Field(..., description="Spending/transaction category")
    description: str = Field(..., description="Short description of transaction")
    status: str = Field(..., description="Status (SUCCESS, PENDING, FAILED)")


class TransactionListResponse(BaseModel):
    """Response containing list of transactions and count."""

    customer_id: str = Field(..., description="Requested customer ID")
    transactions: List[Transaction] = Field(default_factory=list, description="List of transactions")
    count: int = Field(..., description="Number of transactions returned")


class TransactionPeriod(BaseModel):
    """Start and end date period for transaction summary."""

    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class TransactionSummary(BaseModel):
    """Transaction summary response for Customer Insights."""

    customer_id: str = Field(..., description="Requested customer ID")
    period: TransactionPeriod = Field(..., description="Covered time period")
    total_credits: float = Field(..., description="Sum of credit transactions in period")
    total_debits: float = Field(..., description="Sum of debit transactions in period")
    transaction_count: int = Field(..., description="Total transactions in period")
    category_spending: Dict[str, float] = Field(default_factory=dict, description="Debit spending breakdown by category")
    category: Optional[str] = Field(default=None, description="Optional filtered category")
    category_debits: Optional[float] = Field(default=None, description="Total debits in requested category")

"""
Account Pydantic Schemas
"""

from typing import List
from pydantic import BaseModel, Field


class Account(BaseModel):
    """NovaBank Account Model matching data/accounts.json."""

    account_id: str = Field(..., description="Unique account ID (e.g. ACC001)")
    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")
    account_type: str = Field(..., description="Type of account (Savings, Current, Salary)")
    balance: float = Field(..., description="Current account balance in INR")
    currency: str = Field(default="INR", description="Currency (INR)")
    status: str = Field(..., description="Account status (Active, Dormant)")
    opened_date: str = Field(..., description="Account opening date (YYYY-MM-DD)")


class AccountListResponse(BaseModel):
    """Response containing list of accounts for a customer."""

    customer_id: str = Field(..., description="Requested customer ID")
    accounts: List[Account] = Field(default_factory=list, description="List of accounts")


class AccountBalanceItem(BaseModel):
    """Individual account balance item."""

    account_id: str = Field(..., description="Unique account ID")
    account_type: str = Field(..., description="Type of account")
    balance: float = Field(..., description="Current account balance")
    currency: str = Field(default="INR", description="Currency code")
    status: str = Field(..., description="Account status")


class AccountBalanceResponse(BaseModel):
    """Aggregated customer balance response."""

    customer_id: str = Field(..., description="Requested customer ID")
    accounts: List[AccountBalanceItem] = Field(default_factory=list, description="List of customer accounts")
    total_balance: float = Field(..., description="Sum of balances from active accounts")
    currency: str = Field(default="INR", description="Currency code")

"""
Banking Product and Interest Rate Pydantic Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class BankingProduct(BaseModel):
    """NovaBank Banking Product Model matching data/products.json."""

    product_id: str = Field(..., description="Unique product ID (e.g. PROD001)")
    product_name: str = Field(..., description="Product name")
    product_type: str = Field(..., description="Product type (Savings Account, Credit Card, Fixed Deposit, etc.)")
    interest_rate: Optional[float] = Field(None, description="Interest rate percentage")
    minimum_balance: Optional[int] = Field(None, description="Minimum balance requirement in INR")
    annual_fee: Optional[int] = Field(None, description="Annual fee in INR")
    transaction_limit: Optional[int] = Field(None, description="Monthly transaction limit or credit limit")
    eligibility: Optional[str] = Field(None, description="Eligibility criteria")
    tenure: Optional[str] = Field(None, description="Product tenure or duration")


class ProductListResponse(BaseModel):
    """Response containing list of banking products."""

    products: List[BankingProduct] = Field(default_factory=list, description="List of banking products")


class InterestRate(BaseModel):
    """Structured interest rate information."""

    product_id: str = Field(..., description="Associated product or loan ID")
    product_name: str = Field(..., description="Product or loan name")
    product_type: str = Field(..., description="Category or product type")
    interest_rate: float = Field(..., description="Annual interest rate percentage")
    source: Optional[str] = Field(None, description="Source catalog (Product or Loan)")


class InterestRateListResponse(BaseModel):
    """Response containing list of interest rates."""

    interest_rates: List[InterestRate] = Field(default_factory=list, description="List of interest rates")
    rates: Optional[List[InterestRate]] = Field(default_factory=list, description="Convenience alias matching interest_rates")

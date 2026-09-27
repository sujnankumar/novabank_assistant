"""
Loan Pydantic Schemas
"""

from typing import List
from pydantic import BaseModel, Field


class LoanProduct(BaseModel):
    """NovaBank Loan Product Model matching data/loans.json."""

    loan_id: str = Field(..., description="Unique loan product ID (e.g. LOAN001)")
    loan_name: str = Field(..., description="Loan product name")
    loan_type: str = Field(..., description="Loan category (Home Loan, Personal Loan, etc.)")
    minimum_amount: int = Field(..., description="Minimum loan amount in INR")
    maximum_amount: int = Field(..., description="Maximum loan amount in INR")
    interest_rate: float = Field(..., description="Annual interest rate percentage")
    minimum_income: int = Field(..., description="Minimum monthly income required in INR")
    minimum_credit_score: int = Field(..., description="Minimum required credit score")
    minimum_age: int = Field(..., description="Minimum borrower age")
    maximum_age: int = Field(..., description="Maximum borrower age")
    maximum_tenure_years: int = Field(..., description="Maximum tenure in years")
    processing_fee_percent: float = Field(..., description="Processing fee percentage")
    required_documents: List[str] = Field(default_factory=list, description="List of required documents")


class LoanListResponse(BaseModel):
    """Response containing list of loan products."""

    loans: List[LoanProduct] = Field(default_factory=list, description="List of loan products")


class LoanEligibilityRequest(BaseModel):
    """Request payload for simulated loan eligibility check."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")
    loan_id: str = Field(..., description="Unique loan ID (e.g. LOAN001)")
    requested_amount: float = Field(..., gt=0, description="Requested loan amount in INR")


class LoanEligibilityResponse(BaseModel):
    """Response for simulated loan eligibility check."""

    customer_id: str = Field(..., description="Customer ID")
    loan_id: str = Field(..., description="Loan ID")
    eligible: bool = Field(..., description="Whether eligibility requirements are met")
    requested_amount: float = Field(..., description="Requested loan amount")
    reasons: List[str] = Field(default_factory=list, description="List of reasons or criteria outcomes")
    disclaimer: str = Field(
        default="This is a simulated eligibility result for demonstration purposes and is not a real lending decision.",
        description="Mandatory demonstration disclaimer"
    )

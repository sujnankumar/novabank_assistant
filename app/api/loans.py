"""
Loan API Router
===============
Endpoints for exploring NovaBank loan products and performing simulated eligibility checks.
"""

from typing import Optional
from fastapi import APIRouter, Path, Query, status
from app.schemas.loan import (
    LoanEligibilityRequest,
    LoanEligibilityResponse,
    LoanListResponse,
    LoanProduct,
)
from app.services.loan_service import loan_service

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.get(
    "",
    response_model=LoanListResponse,
    status_code=status.HTTP_200_OK,
    summary="List loan products",
    description="Retrieve available NovaBank loan products with optional filtering by loan type.",
    responses={
        200: {"description": "List of loan products"},
    },
)
def get_loans(
    loan_type: Optional[str] = Query(None, description="Filter by loan type (e.g. Home Loan, Personal Loan)"),
) -> LoanListResponse:
    """Return list of loan products."""
    return loan_service.get_loans(loan_type=loan_type)


@router.get(
    "/{loan_id}",
    response_model=LoanProduct,
    status_code=status.HTTP_200_OK,
    summary="Get loan product details",
    description="Retrieve detailed terms and eligibility rules for a specific loan product.",
    responses={
        200: {"description": "Loan product found"},
        404: {"description": "Loan not found"},
    },
)
def get_loan(
    loan_id: str = Path(..., description="Unique loan product ID (e.g., LOAN001)"),
) -> LoanProduct:
    """Return loan product details."""
    return loan_service.get_loan(loan_id=loan_id)


@router.post(
    "/check-eligibility",
    response_model=LoanEligibilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Check loan eligibility",
    description="Perform a deterministic simulated eligibility check using customer data and loan criteria.",
    responses={
        200: {"description": "Simulated eligibility check evaluated"},
        404: {"description": "Customer or loan not found"},
        422: {"description": "Validation error in request payload"},
    },
)
def check_loan_eligibility(
    req: LoanEligibilityRequest,
) -> LoanEligibilityResponse:
    """Evaluate customer eligibility against loan criteria."""
    return loan_service.check_eligibility(req)

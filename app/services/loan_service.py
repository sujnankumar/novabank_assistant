"""
Loan Service Layer
==================
Handles loan product catalog retrieval and deterministic simulated eligibility checks.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from app.repositories.json_repository import JSONRepository, repository
from app.schemas.loan import (
    LoanEligibilityRequest,
    LoanEligibilityResponse,
    LoanListResponse,
    LoanProduct,
)


class LoanService:
    def __init__(self, repo: JSONRepository = repository):
        self.repo = repo

    def get_loans(self, loan_type: Optional[str] = None) -> LoanListResponse:
        """Retrieve all loan products, optionally filtered by loan_type."""
        loans_data = self.repo.get_all_loans()
        if loan_type:
            loans_data = [
                loan for loan in loans_data
                if loan.get("loan_type", "").lower() == loan_type.lower()
                or loan_type.lower() in loan.get("loan_type", "").lower()
            ]

        loans = [LoanProduct(**l) for l in loans_data]
        return LoanListResponse(loans=loans)

    def get_loan(self, loan_id: str) -> LoanProduct:
        """Retrieve a specific loan product by loan_id or raise 404."""
        loan_data = self.repo.get_loan_by_id(loan_id)
        if not loan_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )
        return LoanProduct(**loan_data)

    def check_eligibility(self, req: LoanEligibilityRequest) -> LoanEligibilityResponse:
        """
        Perform deterministic simulated loan eligibility check.
        Uses customer profile and loan criteria.
        """
        # Validate customer
        customer = self.repo.get_customer_by_id(req.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        # Validate loan
        loan = self.repo.get_loan_by_id(req.loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )

        cust_income = float(customer.get("monthly_income", 0))
        cust_credit = int(customer.get("credit_score", 0))
        cust_age = int(customer.get("age", 0))

        min_income = float(loan.get("minimum_income", 0))
        min_credit = int(loan.get("minimum_credit_score", 0))
        min_age = int(loan.get("minimum_age", 18))
        max_age = int(loan.get("maximum_age", 100))
        min_amount = float(loan.get("minimum_amount", 0))
        max_amount = float(loan.get("maximum_amount", 0))

        failure_reasons: List[str] = []

        # 1. Income Check
        if cust_income < min_income:
            failure_reasons.append("Monthly income is below the minimum required income")

        # 2. Credit Score Check
        if cust_credit < min_credit:
            failure_reasons.append("Credit score is below the minimum required score")

        # 3. Age Check
        if cust_age < min_age:
            failure_reasons.append("Age is below the minimum required age")
        elif cust_age > max_age:
            failure_reasons.append("Age exceeds the maximum permitted age")

        # 4. Amount Check
        if req.requested_amount < min_amount:
            failure_reasons.append("Requested amount is below the minimum loan amount")
        elif req.requested_amount > max_amount:
            failure_reasons.append("Requested amount exceeds the maximum loan amount")

        # Check outcome
        if not failure_reasons:
            eligible = True
            reasons = [
                "Minimum income requirement satisfied",
                "Minimum credit score requirement satisfied",
                "Age requirement satisfied",
                "Requested amount is within the permitted range",
            ]
        else:
            eligible = False
            reasons = failure_reasons

        disclaimer = "This is a simulated eligibility result for demonstration purposes and is not a real lending decision."

        return LoanEligibilityResponse(
            customer_id=req.customer_id,
            loan_id=req.loan_id,
            eligible=eligible,
            requested_amount=req.requested_amount,
            reasons=reasons,
            disclaimer=disclaimer,
        )


loan_service = LoanService()

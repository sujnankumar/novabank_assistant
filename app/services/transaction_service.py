"""
Transaction Service Layer
=========================
Handles business logic for transaction listing, filtering, data isolation,
and transaction summaries for Customer Insights.
"""

from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from app.repositories.json_repository import JSONRepository, repository
from app.schemas.transaction import (
    Transaction,
    TransactionListResponse,
    TransactionPeriod,
    TransactionSummary,
)


class TransactionService:
    def __init__(self, repo: JSONRepository = repository):
        self.repo = repo

    def _validate_date(self, date_str: str, param_name: str) -> None:
        """Validate date format is YYYY-MM-DD."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {param_name} format. Expected YYYY-MM-DD."
            )

    def _validate_date_range(self, start_date: Optional[str], end_date: Optional[str]) -> None:
        """Ensure start_date <= end_date."""
        if start_date:
            self._validate_date(start_date, "start_date")
        if end_date:
            self._validate_date(end_date, "end_date")
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date range: start_date cannot be after end_date."
            )

    def get_transactions(
        self,
        customer_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> TransactionListResponse:
        """
        Retrieve filtered transactions for customer_id with strict data isolation.
        Newest transactions are returned first.
        """
        if not self.repo.customer_exists(customer_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        self._validate_date_range(start_date, end_date)

        # Retrieve isolated customer transactions (checked against customer accounts)
        raw_txns = self.repo.get_transactions_by_customer_id(customer_id)

        # Apply filters
        filtered: List[Dict] = []
        for t in raw_txns:
            if transaction_type and t.get("type", "").upper() != transaction_type.upper():
                continue
            if category and t.get("category", "").lower() != category.lower():
                continue
            if merchant and merchant.lower() not in t.get("merchant", "").lower():
                continue
            if start_date and t.get("date", "") < start_date:
                continue
            if end_date and t.get("date", "") > end_date:
                continue
            if status_filter and t.get("status", "").upper() != status_filter.upper():
                continue
            filtered.append(t)

        # Order by date descending (newest first), then transaction_id descending
        filtered.sort(key=lambda x: (x.get("date", ""), x.get("transaction_id", "")), reverse=True)

        total_matching = len(filtered)
        paged_txns = filtered[offset : offset + limit]

        transactions = [Transaction(**t) for t in paged_txns]

        return TransactionListResponse(
            customer_id=customer_id,
            transactions=transactions,
            count=len(transactions),
        )

    def get_transactions_summary(
        self,
        customer_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> TransactionSummary:
        """
        Generate financial summary for customer transactions over a given period.
        Calculates total credits, total debits, count, and category spending (debits).
        """
        if not self.repo.customer_exists(customer_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        self._validate_date_range(start_date, end_date)

        raw_txns = self.repo.get_transactions_by_customer_id(customer_id)

        # Filter by date range
        filtered: List[Dict] = []
        for t in raw_txns:
            if start_date and t.get("date", "") < start_date:
                continue
            if end_date and t.get("date", "") > end_date:
                continue
            filtered.append(t)

        total_credits = 0.0
        total_debits = 0.0
        category_spending: Dict[str, float] = {}

        for t in filtered:
            amount = float(t.get("amount", 0.0))
            txn_type = t.get("type", "").upper()
            category = t.get("category", "Other")

            if txn_type == "CREDIT":
                total_credits += amount
            elif txn_type == "DEBIT":
                total_debits += amount
                category_spending[category] = category_spending.get(category, 0.0) + amount

        # Round all monetary sums
        total_credits = round(total_credits, 2)
        total_debits = round(total_debits, 2)
        for cat in list(category_spending.keys()):
            category_spending[cat] = round(category_spending[cat], 2)

        # Determine period bounds
        if start_date or end_date:
            actual_start = start_date
            actual_end = end_date
        elif filtered:
            dates = [t["date"] for t in filtered if "date" in t]
            actual_start = min(dates) if dates else None
            actual_end = max(dates) if dates else None
        else:
            actual_start = None
            actual_end = None

        period = TransactionPeriod(start_date=actual_start, end_date=actual_end)

        return TransactionSummary(
            customer_id=customer_id,
            period=period,
            total_credits=total_credits,
            total_debits=total_debits,
            transaction_count=len(filtered),
            category_spending=category_spending,
        )


transaction_service = TransactionService()

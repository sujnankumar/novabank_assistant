"""
Transaction API Router
======================
Endpoints for querying customer transactions and generating transaction summaries.
"""

from typing import Optional
from fastapi import APIRouter, Path, Query, status
from app.schemas.transaction import TransactionListResponse, TransactionSummary
from app.services.transaction_service import transaction_service

router = APIRouter(prefix="/accounts", tags=["Transactions"])


@router.get(
    "/{customer_id}/transactions/summary",
    response_model=TransactionSummary,
    status_code=status.HTTP_200_OK,
    summary="Get transaction summary",
    description="Calculate credit/debit totals and category spending for a customer over an optional period.",
    responses={
        200: {"description": "Summary calculated successfully"},
        400: {"description": "Invalid date range or format"},
        404: {"description": "Customer not found"},
    },
)
def get_transactions_summary(
    customer_id: str = Path(..., description="Unique customer ID (e.g., CUST001)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
) -> TransactionSummary:
    """Return transaction summary and spending analysis."""
    return transaction_service.get_transactions_summary(
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{customer_id}/transactions",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get customer transactions",
    description="Retrieve paginated transaction history for a customer with optional filters.",
    responses={
        200: {"description": "Transactions retrieved"},
        400: {"description": "Invalid date range or format"},
        404: {"description": "Customer not found"},
    },
)
def get_transactions(
    customer_id: str = Path(..., description="Unique customer ID (e.g., CUST001)"),
    limit: int = Query(5, ge=1, le=100, description="Max transactions to return (1-100, default: 5)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    transaction_type: Optional[str] = Query(None, description="Filter by type (CREDIT or DEBIT)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    merchant: Optional[str] = Query(None, description="Filter by merchant"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (SUCCESS, PENDING, FAILED)"),
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    sort: str = Query("desc", description="Sort order ('desc' or 'asc')"),
) -> TransactionListResponse:
    """Return customer transactions."""
    return transaction_service.get_transactions(
        customer_id=customer_id,
        limit=limit,
        offset=offset,
        transaction_type=transaction_type,
        category=category,
        merchant=merchant,
        start_date=start_date,
        end_date=end_date,
        status_filter=status_filter,
        account_id=account_id,
        sort=sort,
    )

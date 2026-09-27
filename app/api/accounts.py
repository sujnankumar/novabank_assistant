"""
Account API Router
==================
Endpoints for retrieving customer accounts and calculated balance information.
"""

from fastapi import APIRouter, Path, status
from app.schemas.account import AccountBalanceResponse, AccountListResponse
from app.services.account_service import account_service

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get(
    "/{customer_id}",
    response_model=AccountListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get customer accounts",
    description="Retrieve all bank accounts belonging to a specific customer.",
    responses={
        200: {"description": "List of accounts for customer"},
        404: {"description": "Customer not found"},
    },
)
def get_accounts(
    customer_id: str = Path(..., description="Unique customer ID (e.g., CUST001)")
) -> AccountListResponse:
    """Return all accounts for the requested customer."""
    return account_service.get_accounts(customer_id)


@router.get(
    "/{customer_id}/balance",
    response_model=AccountBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get account balance",
    description="Retrieve balance information and calculate total balance across active accounts.",
    responses={
        200: {"description": "Account balances and total balance calculated"},
        404: {"description": "Customer not found"},
    },
)
def get_balance(
    customer_id: str = Path(..., description="Unique customer ID (e.g., CUST001)")
) -> AccountBalanceResponse:
    """Return customer account balances and total active balance."""
    return account_service.get_balance(customer_id)

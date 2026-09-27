"""
Account Service Layer
=====================
Handles business logic for account listing and balance calculations.
"""

from fastapi import HTTPException, status
from app.repositories.json_repository import JSONRepository, repository
from app.schemas.account import (
    Account,
    AccountBalanceItem,
    AccountBalanceResponse,
    AccountListResponse,
)


class AccountService:
    def __init__(self, repo: JSONRepository = repository):
        self.repo = repo

    def get_accounts(self, customer_id: str) -> AccountListResponse:
        """Retrieve all accounts for a customer. Returns 404 if customer does not exist."""
        if not self.repo.customer_exists(customer_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        accounts_data = self.repo.get_accounts_by_customer_id(customer_id)
        accounts = [Account(**acc) for acc in accounts_data]
        return AccountListResponse(customer_id=customer_id, accounts=accounts)

    def get_balance(self, customer_id: str) -> AccountBalanceResponse:
        """
        Calculate total active balance and list account balances for a customer.
        Only active accounts contribute to total_balance.
        """
        if not self.repo.customer_exists(customer_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        accounts_data = self.repo.get_accounts_by_customer_id(customer_id)

        balance_items = []
        total_balance = 0.0

        for acc in accounts_data:
            balance_items.append(
                AccountBalanceItem(
                    account_id=acc["account_id"],
                    account_type=acc["account_type"],
                    balance=float(acc["balance"]),
                    currency=acc.get("currency", "INR"),
                    status=acc["status"],
                )
            )
            # Only ACTIVE accounts contribute to total balance
            if acc.get("status", "").strip().upper() == "ACTIVE":
                total_balance += float(acc["balance"])

        total_balance = round(total_balance, 2)

        return AccountBalanceResponse(
            customer_id=customer_id,
            accounts=balance_items,
            total_balance=total_balance,
            currency="INR",
        )


account_service = AccountService()

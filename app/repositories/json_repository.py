"""
NovaBank JSON Repository
=========================
Modular data-access layer for loading and querying synthetic banking datasets.
Reads data directly from JSON files in the data/ directory.
Enforces customer data isolation and referential integrity.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class JSONRepository:
    """Repository for querying NovaBank synthetic JSON data files."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is not None:
            self.data_dir = Path(data_dir)
        elif os.environ.get("NOVABANK_DATA_DIR"):
            self.data_dir = Path(os.environ["NOVABANK_DATA_DIR"])
        else:
            # Default to project root / data
            self.data_dir = Path(__file__).resolve().parent.parent.parent / "data"

        self._customers: List[Dict[str, Any]] = []
        self._customer_profiles: List[Dict[str, Any]] = []
        self._accounts: List[Dict[str, Any]] = []
        self._transactions: List[Dict[str, Any]] = []
        self._loans: List[Dict[str, Any]] = []
        self._products: List[Dict[str, Any]] = []

        self.reload()

    def _load_json(self, filename: str) -> List[Dict[str, Any]]:
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def reload(self) -> None:
        """Reload all datasets from disk."""
        self._customers = self._load_json("customers.json")
        self._customer_profiles = self._load_json("customer_profiles.json")
        self._accounts = self._load_json("accounts.json")
        self._transactions = self._load_json("transactions.json")
        self._loans = self._load_json("loans.json")
        self._products = self._load_json("products.json")

    # ==================== Customers ====================

    def get_all_customers(self) -> List[Dict[str, Any]]:
        """Return all customers."""
        return list(self._customers)

    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Return customer by customer_id or None if not found."""
        for c in self._customers:
            if c.get("customer_id") == customer_id:
                return dict(c)
        return None

    def customer_exists(self, customer_id: str) -> bool:
        """Check if customer_id exists."""
        return any(c.get("customer_id") == customer_id for c in self._customers)

    # ==================== Customer Profiles ====================

    def get_profile_by_customer_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Return customer profile by customer_id or None if not found."""
        for p in self._customer_profiles:
            if p.get("customer_id") == customer_id:
                return dict(p)
        return None

    # ==================== Accounts ====================

    def get_accounts_by_customer_id(self, customer_id: str) -> List[Dict[str, Any]]:
        """Return all accounts belonging strictly to customer_id."""
        return [dict(a) for a in self._accounts if a.get("customer_id") == customer_id]

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Return account by account_id or None if not found."""
        for a in self._accounts:
            if a.get("account_id") == account_id:
                return dict(a)
        return None

    def get_customer_account_ids(self, customer_id: str) -> Set[str]:
        """Return set of account_ids belonging to customer_id."""
        return {a["account_id"] for a in self._accounts if a.get("customer_id") == customer_id}

    # ==================== Transactions ====================

    def get_transactions_by_customer_id(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Return transactions belonging to customer_id with strict isolation check.
        Both conditions must be met:
          1. transaction.customer_id == requested_customer_id
          2. transaction.account_id belongs to requested_customer_id
        """
        valid_account_ids = self.get_customer_account_ids(customer_id)
        isolated_txns = []
        for t in self._transactions:
            if t.get("customer_id") == customer_id and t.get("account_id") in valid_account_ids:
                isolated_txns.append(dict(t))
        return isolated_txns

    # ==================== Loans ====================

    def get_all_loans(self) -> List[Dict[str, Any]]:
        """Return all loan products."""
        return list(self._loans)

    def get_loan_by_id(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Return loan product by loan_id or None if not found."""
        for loan in self._loans:
            if loan.get("loan_id") == loan_id:
                return dict(loan)
        return None

    # ==================== Products ====================

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Return all banking products."""
        return list(self._products)

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Return product by product_id or None if not found."""
        for p in self._products:
            if p.get("product_id") == product_id:
                return dict(p)
        return None


# Global repository instance
repository = JSONRepository()

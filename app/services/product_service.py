"""
Product Service Layer
=====================
Handles product catalog queries and structured interest rate information retrieval.
"""

from typing import List, Optional
from app.repositories.json_repository import JSONRepository, repository
from app.schemas.product import (
    BankingProduct,
    InterestRate,
    InterestRateListResponse,
    ProductListResponse,
)


class ProductService:
    def __init__(self, repo: JSONRepository = repository):
        self.repo = repo

    def get_products(self, product_type: Optional[str] = None) -> ProductListResponse:
        """Retrieve all banking products, optionally filtered by product_type."""
        products_data = self.repo.get_all_products()
        if product_type:
            pt_clean = product_type.strip().lower()
            products_data = [
                p for p in products_data
                if pt_clean == p.get("product_type", "").lower()
                or pt_clean in p.get("product_type", "").lower()
            ]

        products = [BankingProduct(**p) for p in products_data]
        return ProductListResponse(products=products)

    def get_interest_rates(self, product_type: Optional[str] = None) -> InterestRateListResponse:
        """
        Retrieve current synthetic NovaBank interest rates directly from structured data.
        Combines rates from products.json and loans.json.
        """
        all_rates: List[InterestRate] = []

        # From products.json
        for p in self.repo.get_all_products():
            if "interest_rate" in p and p["interest_rate"] is not None:
                all_rates.append(
                    InterestRate(
                        product_id=p["product_id"],
                        product_name=p["product_name"],
                        product_type=p["product_type"],
                        interest_rate=float(p["interest_rate"]),
                        source="Product",
                    )
                )

        # From loans.json
        for l in self.repo.get_all_loans():
            if "interest_rate" in l and l["interest_rate"] is not None:
                all_rates.append(
                    InterestRate(
                        product_id=l["loan_id"],
                        product_name=l["loan_name"],
                        product_type=l["loan_type"],
                        interest_rate=float(l["interest_rate"]),
                        source="Loan",
                    )
                )

        if product_type:
            pt_clean = product_type.strip().lower()
            all_rates = [
                r for r in all_rates
                if pt_clean == r.product_type.lower()
                or pt_clean in r.product_type.lower()
            ]

        return InterestRateListResponse(
            interest_rates=all_rates,
            rates=all_rates,
        )


product_service = ProductService()

"""
Customer Service Layer
======================
Handles business logic for customer lookup and profile retrieval.
"""

from fastapi import HTTPException, status
from app.repositories.json_repository import JSONRepository, repository
from app.schemas.customer import Customer, CustomerProfile


class CustomerService:
    def __init__(self, repo: JSONRepository = repository):
        self.repo = repo

    def get_customer(self, customer_id: str) -> Customer:
        """Retrieve customer by customer_id or raise 404."""
        customer_data = self.repo.get_customer_by_id(customer_id)
        if not customer_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return Customer(**customer_data)

    def get_customer_profile(self, customer_id: str) -> CustomerProfile:
        """Retrieve customer profile by customer_id or raise 404."""
        # First ensure customer exists
        if not self.repo.customer_exists(customer_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        profile_data = self.repo.get_profile_by_customer_id(customer_id)
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found"
            )
        return CustomerProfile(**profile_data)


customer_service = CustomerService()

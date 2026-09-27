"""
Customer API Router
===================
Endpoints for retrieving customer profile and demographic information.
"""

from typing import List
from fastapi import APIRouter, Path, status
from app.schemas.customer import Customer, CustomerProfile
from app.services.customer_service import customer_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get(
    "",
    response_model=List[Customer],
    status_code=status.HTTP_200_OK,
    summary="List all customers",
    description="Retrieve all synthetic NovaBank customers from data store.",
)
def list_customers() -> List[Customer]:
    """Return all synthetic customers."""
    return [Customer(**c) for c in customer_service.repo.get_all_customers()]


@router.get(
    "/{customer_id}",
    response_model=Customer,
    status_code=status.HTTP_200_OK,
    summary="Get customer details",
    description="Retrieve basic information about a synthetic NovaBank customer by their customer ID.",
    responses={
        200: {"description": "Customer found and returned"},
        404: {"description": "Customer not found"},
    },
)
def get_customer(
    customer_id: str = Path(..., description="Unique customer ID (e.g., CUST001)")
) -> Customer:
    """Return basic customer details."""
    return customer_service.get_customer(customer_id)


@router.get(
    "/{customer_id}/profile",
    response_model=CustomerProfile,
    status_code=status.HTTP_200_OK,
    summary="Get customer profile",
    description="Retrieve customer profile and personalization preferences by customer ID.",
    responses={
        200: {"description": "Customer profile found and returned"},
        404: {"description": "Customer or customer profile not found"},
    },
)
def get_customer_profile(
    customer_id: str = Path(..., description="Unique customer ID (e.g., CUST001)")
) -> CustomerProfile:
    """Return customer profile and preferences."""
    return customer_service.get_customer_profile(customer_id)

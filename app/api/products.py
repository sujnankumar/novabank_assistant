"""
Product and Interest Rate API Router
====================================
Endpoints for exploring NovaBank banking products and checking current interest rates.
"""

from typing import Optional
from fastapi import APIRouter, Query, status
from app.schemas.product import InterestRateListResponse, ProductListResponse
from app.services.product_service import product_service

router = APIRouter(tags=["Products & Rates"])


@router.get(
    "/products",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List banking products",
    description="Retrieve available NovaBank banking products (Savings, FDs, Credit Cards, etc.).",
    responses={
        200: {"description": "List of banking products"},
    },
)
def get_products(
    product_type: Optional[str] = Query(None, description="Filter by product type (e.g. Savings, Credit Card, Fixed Deposit)"),
) -> ProductListResponse:
    """Return catalog of banking products."""
    return product_service.get_products(product_type=product_type)


@router.get(
    "/interest-rates",
    response_model=InterestRateListResponse,
    status_code=status.HTTP_200_OK,
    summary="List interest rates",
    description="Retrieve current synthetic NovaBank interest rates derived from products and loan datasets.",
    responses={
        200: {"description": "List of interest rates"},
    },
)
def get_interest_rates(
    product_type: Optional[str] = Query(None, description="Filter by product or loan type (e.g. Home Loan, Savings Account)"),
) -> InterestRateListResponse:
    """Return interest rates across products and loans."""
    return product_service.get_interest_rates(product_type=product_type)

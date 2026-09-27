"""
Health API Router
=================
Lightweight endpoint for API availability checks.
Phase 8 Implementation.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Health status response model."""

    status: str = "ok"


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Lightweight health check confirming API operational status without running heavy tasks.",
    responses={
        200: {"description": "API is operational"},
    },
)
def health_check() -> HealthResponse:
    """Returns lightweight system health status."""
    return HealthResponse(status="ok")

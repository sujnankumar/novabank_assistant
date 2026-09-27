"""
Customer Pydantic Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class Customer(BaseModel):
    """NovaBank Customer Model matching data/customers.json."""

    customer_id: str = Field(..., description="Unique customer ID (e.g. CUST001)")
    name: str = Field(..., description="Full customer name")
    age: int = Field(..., ge=18, description="Customer age")
    gender: str = Field(..., description="Gender")
    city: str = Field(..., description="Residential city")
    occupation: str = Field(..., description="Customer occupation")
    monthly_income: float = Field(..., ge=0, description="Monthly income in INR")
    credit_score: int = Field(..., ge=300, le=900, description="Credit score")
    consent: bool = Field(..., description="Consent for data processing")


class CustomerProfile(BaseModel):
    """NovaBank Customer Profile Model matching data/customer_profiles.json."""

    customer_id: str = Field(..., description="Unique customer ID referencing Customer")
    preferred_language: str = Field(..., description="Preferred communication language")
    communication_preference: str = Field(..., description="Channel preference (Email, WhatsApp, Phone Call, SMS)")
    customer_segment: str = Field(..., description="Customer tier segment (Standard, Premium, Gold, Platinum)")
    employment_type: str = Field(..., description="Employment type (Salaried, Self-Employed, etc.)")
    relationship_years: int = Field(..., ge=0, description="Years with NovaBank")
    consent_for_personalization: bool = Field(..., description="Personalization consent flag")

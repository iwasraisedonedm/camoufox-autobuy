"""Validated control-plane request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from autobuy.domain.enums import CustomerStatus, EntitlementStatus


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime


class EntitlementGrant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: UUID
    retailer_offering_id: UUID
    starts_at: datetime
    expires_at: datetime
    concurrent_job_limit: int = Field(ge=1, le=100)
    successful_unit_allowance_total: int = Field(ge=1, le=10_000)
    external_grant_reference: str = Field(min_length=1, max_length=160)


class EntitlementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    retailer_offering_id: UUID
    starts_at: datetime
    expires_at: datetime
    concurrent_job_limit: int
    successful_unit_allowance_total: int
    successful_unit_allowance_used: int
    status: EntitlementStatus
    external_grant_reference: str
    created_at: datetime

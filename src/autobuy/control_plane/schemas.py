"""Validated control-plane request and response schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from autobuy.domain.enums import (
    CustomerStatus,
    EntitlementStatus,
    JobStatus,
    LeaseStatus,
    WorkerStatus,
    WorkflowMode,
)


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


class PurchaseTargetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: UUID
    retailer_offering_id: UUID
    retailer_product_id: str = Field(min_length=1, max_length=160)
    retailer_variant_id: str | None = Field(default=None, max_length=160)
    url: str = Field(min_length=1, max_length=2048)
    display_name: str | None = Field(default=None, max_length=300)


class PurchaseTargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    retailer_offering_id: UUID
    retailer_product_id: str
    retailer_variant_id: str | None
    url: str
    display_name: str | None
    created_at: datetime
    updated_at: datetime


class MonitoringJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: UUID
    entitlement_id: UUID
    retailer_profile_id: UUID
    purchase_target_id: UUID
    workflow_mode: str
    max_unit_price: Decimal = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    quantity_requested: int = Field(ge=1, le=100)
    success_limit: int = Field(default=1, ge=1, le=100)
    expires_at: datetime


class MonitoringJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    entitlement_id: UUID
    retailer_profile_id: UUID
    purchase_target_id: UUID
    workflow_mode: WorkflowMode
    max_unit_price: Decimal
    currency: str
    quantity_requested: int
    success_limit: int
    expires_at: datetime
    status: JobStatus
    version: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class OrderConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retailer_order_reference: str = Field(min_length=1, max_length=200)
    quantity_confirmed: int = Field(ge=1, le=100)
    unit_price: Decimal | None = Field(default=None, gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    confirmed_at: datetime


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    retailer_profile_id: UUID
    job_id: UUID
    purchase_attempt_id: UUID
    retailer_order_reference: str
    quantity_confirmed: int
    unit_price: Decimal | None
    currency: str
    confirmed_at: datetime
    created_at: datetime


class WorkerRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instance_id: str = Field(min_length=1, max_length=160)
    version: str = Field(min_length=1, max_length=64)


class WorkerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    instance_id: str
    status: WorkerStatus
    version: str
    last_heartbeat_at: datetime
    started_at: datetime


class LeaseAcquireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: UUID
    retailer_profile_id: UUID


class LeaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    worker_id: UUID
    retailer_profile_id: UUID
    acquired_at: datetime
    expires_at: datetime
    released_at: datetime | None
    status: LeaseStatus


class LeaseAcquireResponse(LeaseRead):
    lease_token: str


class LeaseMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: UUID
    lease_token: str = Field(min_length=32, max_length=512)


class LeaseReapResponse(BaseModel):
    expired_leases: int = Field(ge=0)


class ProfileArtifactAccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: UUID
    lease_id: UUID
    lease_token: str = Field(min_length=32, max_length=512)


class ProfileArtifactMetadataRead(BaseModel):
    profile_id: UUID
    encrypted_artifact_ref: str | None
    artifact_version: int = Field(ge=0)


class ProfileArtifactCheckpointRequest(ProfileArtifactAccessRequest):
    encrypted_artifact_ref: str = Field(min_length=1, max_length=2048)
    artifact_version: int = Field(ge=1)


class JobAssignmentRead(BaseModel):
    job_id: UUID
    retailer_code: str
    retailer_profile_id: UUID
    purchase_target_id: UUID
    retailer_product_id: str
    retailer_variant_id: str | None
    product_url: str
    workflow_mode: WorkflowMode
    max_unit_price: Decimal
    currency: str
    quantity_requested: int
    expires_at: datetime

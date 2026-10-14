"""Authoritative SQLAlchemy models for durable platform state."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from autobuy.domain.enums import (
    AttemptStatus,
    CustomerStatus,
    EntitlementStatus,
    JobStatus,
    LeaseStatus,
    RetailerHealth,
    RetailerProfileStatus,
    WorkerStatus,
    WorkflowMode,
)
from autobuy.persistence.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)


class CustomerAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_accounts"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    status: Mapped[CustomerStatus] = mapped_column(
        SAEnum(CustomerStatus, native_enum=False, validate_strings=True),
        default=CustomerStatus.ACTIVE,
        nullable=False,
    )
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DiscordIdentity(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "discord_identities"

    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    discord_user_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RetailerOffering(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retailer_offerings"

    retailer_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    adapter_version: Mapped[str] = mapped_column(
        String(64), default="0.1.0", nullable=False
    )


class ServiceEntitlement(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "service_entitlements"
    __table_args__ = (
        CheckConstraint("successful_unit_allowance_total >= 0"),
        CheckConstraint("successful_unit_allowance_used >= 0"),
        CheckConstraint(
            "successful_unit_allowance_used <= successful_unit_allowance_total"
        ),
        CheckConstraint("concurrent_job_limit >= 0"),
        CheckConstraint("expires_at > starts_at"),
        Index(
            "ix_entitlements_customer_retailer_status",
            "customer_id",
            "retailer_offering_id",
            "status",
        ),
    )

    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    retailer_offering_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retailer_offerings.id", ondelete="RESTRICT"),
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    concurrent_job_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    successful_unit_allowance_total: Mapped[int] = mapped_column(Integer, nullable=False)
    successful_unit_allowance_used: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    status: Mapped[EntitlementStatus] = mapped_column(
        SAEnum(EntitlementStatus, native_enum=False, validate_strings=True),
        default=EntitlementStatus.PENDING,
        nullable=False,
        index=True,
    )
    external_grant_reference: Mapped[str] = mapped_column(
        String(160), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class RetailerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retailer_profiles"
    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "retailer_offering_id",
            "label",
            name="uq_retailer_profile_customer_retailer_label",
        ),
    )

    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    retailer_offering_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retailer_offerings.id", ondelete="RESTRICT"),
        index=True,
    )
    label: Mapped[str] = mapped_column(String(80), default="default", nullable=False)
    status: Mapped[RetailerProfileStatus] = mapped_column(
        SAEnum(RetailerProfileStatus, native_enum=False, validate_strings=True),
        default=RetailerProfileStatus.DISCONNECTED,
        nullable=False,
        index=True,
    )
    encrypted_artifact_ref: Mapped[str | None] = mapped_column(Text)
    artifact_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_authenticated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountLinkSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "account_link_sessions"

    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    retailer_offering_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retailer_offerings.id", ondelete="CASCADE"),
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PurchaseTarget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_targets"
    __table_args__ = (
        Index(
            "ix_target_identity",
            "customer_id",
            "retailer_offering_id",
            "retailer_product_id",
            "retailer_variant_id",
        ),
    )

    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    retailer_offering_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retailer_offerings.id", ondelete="RESTRICT"),
        index=True,
    )
    retailer_product_id: Mapped[str] = mapped_column(String(160), nullable=False)
    retailer_variant_id: Mapped[str | None] = mapped_column(String(160))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(300))


class MonitoringJob(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "monitoring_jobs"
    __table_args__ = (
        CheckConstraint("quantity_requested > 0"),
        CheckConstraint("success_limit > 0"),
        CheckConstraint("max_unit_price > 0"),
        Index("ix_jobs_customer_status", "customer_id", "status"),
    )

    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    entitlement_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service_entitlements.id", ondelete="RESTRICT"),
        index=True,
    )
    retailer_profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retailer_profiles.id", ondelete="RESTRICT"),
        index=True,
    )
    purchase_target_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("purchase_targets.id", ondelete="RESTRICT"),
        index=True,
    )
    workflow_mode: Mapped[WorkflowMode] = mapped_column(
        SAEnum(WorkflowMode, native_enum=False, validate_strings=True),
        nullable=False,
    )
    max_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    quantity_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    success_limit: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, native_enum=False, validate_strings=True),
        default=JobStatus.CREATED,
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PurchaseAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "purchase_attempts"
    __table_args__ = (
        UniqueConstraint("job_id", "attempt_number", name="uq_attempt_job_number"),
        Index("ix_attempt_job_state", "job_id", "state"),
    )

    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitoring_jobs.id", ondelete="CASCADE"),
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[AttemptStatus] = mapped_column(
        SAEnum(AttemptStatus, native_enum=False, validate_strings=True),
        default=AttemptStatus.CREATED,
        nullable=False,
    )
    observed_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    quantity_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(80))
    reference_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ambiguous_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Order(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint(
            "retailer_profile_id",
            "retailer_order_reference",
            name="uq_order_retailer_profile_reference",
        ),
        CheckConstraint("quantity_confirmed > 0"),
    )

    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customer_accounts.id", ondelete="RESTRICT"),
        index=True,
    )
    retailer_profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retailer_profiles.id", ondelete="RESTRICT"),
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitoring_jobs.id", ondelete="RESTRICT"),
        index=True,
    )
    purchase_attempt_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("purchase_attempts.id", ondelete="RESTRICT"),
        unique=True,
    )
    retailer_order_reference: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    quantity_confirmed: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class JobEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "job_events"
    __table_args__ = (Index("ix_job_events_job_created", "job_id", "created_at"),)

    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitoring_jobs.id", ondelete="CASCADE"),
        index=True,
    )
    attempt_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("purchase_attempts.id", ondelete="SET NULL"),
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class Worker(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "workers"

    instance_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    status: Mapped[WorkerStatus] = mapped_column(
        SAEnum(WorkerStatus, native_enum=False, validate_strings=True),
        default=WorkerStatus.STARTING,
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class WorkerLease(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "worker_leases"
    __table_args__ = (
        Index("ix_worker_lease_profile_status", "retailer_profile_id", "status"),
        Index(
            "uq_active_lease_per_profile",
            "retailer_profile_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    worker_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        index=True,
    )
    retailer_profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retailer_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    lease_token_hash: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[LeaseStatus] = mapped_column(
        SAEnum(LeaseStatus, native_enum=False, validate_strings=True),
        default=LeaseStatus.ACTIVE,
        nullable=False,
        index=True,
    )


class RetailerHealthSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "retailer_health_snapshots"
    __table_args__ = (
        Index("ix_retailer_health_observed", "retailer_offering_id", "observed_at"),
    )

    retailer_offering_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("retailer_offerings.id", ondelete="CASCADE"),
        index=True,
    )
    health_state: Mapped[RetailerHealth] = mapped_column(
        SAEnum(RetailerHealth, native_enum=False, validate_strings=True),
        nullable=False,
    )
    metrics_json: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

"""Create initial AutoBuy platform schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_accounts",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "DISABLED", native_enum=False),
            nullable=False,
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_customer_accounts_email", "customer_accounts", ["email"], unique=True)

    op.create_table(
        "retailer_offerings",
        sa.Column("retailer_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("adapter_version", sa.String(length=64), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("retailer_code"),
    )
    op.create_index(
        "ix_retailer_offerings_retailer_code",
        "retailer_offerings",
        ["retailer_code"],
        unique=True,
    )

    op.create_table(
        "workers",
        sa.Column("instance_id", sa.String(length=160), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "STARTING",
                "REGISTERED",
                "IDLE",
                "LEASED",
                "RUNNING",
                "DRAINING",
                "STOPPED",
                "LOST",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id"),
    )
    op.create_index("ix_workers_last_heartbeat_at", "workers", ["last_heartbeat_at"])
    op.create_index("ix_workers_status", "workers", ["status"])

    op.create_table(
        "discord_identities",
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("discord_user_id", sa.String(length=32), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customer_accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discord_user_id"),
    )
    op.create_index(
        "ix_discord_identities_customer_id",
        "discord_identities",
        ["customer_id"],
    )
    op.create_index(
        "ix_discord_identities_discord_user_id",
        "discord_identities",
        ["discord_user_id"],
        unique=True,
    )

    op.create_table(
        "service_entitlements",
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_offering_id", sa.Uuid(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concurrent_job_limit", sa.Integer(), nullable=False),
        sa.Column("successful_unit_allowance_total", sa.Integer(), nullable=False),
        sa.Column("successful_unit_allowance_used", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "ACTIVE",
                "EXHAUSTED",
                "EXPIRED",
                "REVOKED",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("external_grant_reference", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("concurrent_job_limit >= 0"),
        sa.CheckConstraint("expires_at > starts_at"),
        sa.CheckConstraint("successful_unit_allowance_total >= 0"),
        sa.CheckConstraint("successful_unit_allowance_used >= 0"),
        sa.CheckConstraint(
            "successful_unit_allowance_used <= successful_unit_allowance_total"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customer_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["retailer_offering_id"], ["retailer_offerings.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_grant_reference"),
    )
    op.create_index(
        "ix_entitlements_customer_retailer_status",
        "service_entitlements",
        ["customer_id", "retailer_offering_id", "status"],
    )
    op.create_index(
        "ix_service_entitlements_customer_id",
        "service_entitlements",
        ["customer_id"],
    )
    op.create_index(
        "ix_service_entitlements_retailer_offering_id",
        "service_entitlements",
        ["retailer_offering_id"],
    )
    op.create_index(
        "ix_service_entitlements_status",
        "service_entitlements",
        ["status"],
    )

    op.create_table(
        "retailer_profiles",
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_offering_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DISCONNECTED",
                "LINK_PENDING",
                "AUTHENTICATED",
                "READY",
                "REAUTH_REQUIRED",
                "LOCKED",
                "DISCONNECTING",
                "ERROR",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("encrypted_artifact_ref", sa.Text(), nullable=True),
        sa.Column("artifact_version", sa.Integer(), nullable=False),
        sa.Column("last_authenticated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customer_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["retailer_offering_id"], ["retailer_offerings.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_id",
            "retailer_offering_id",
            "label",
            name="uq_retailer_profile_customer_retailer_label",
        ),
    )
    op.create_index(
        "ix_retailer_profiles_customer_id", "retailer_profiles", ["customer_id"]
    )
    op.create_index(
        "ix_retailer_profiles_retailer_offering_id",
        "retailer_profiles",
        ["retailer_offering_id"],
    )
    op.create_index("ix_retailer_profiles_status", "retailer_profiles", ["status"])

    op.create_table(
        "account_link_sessions",
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_offering_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customer_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["retailer_offering_id"], ["retailer_offerings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_account_link_sessions_customer_id",
        "account_link_sessions",
        ["customer_id"],
    )
    op.create_index(
        "ix_account_link_sessions_expires_at",
        "account_link_sessions",
        ["expires_at"],
    )
    op.create_index(
        "ix_account_link_sessions_retailer_offering_id",
        "account_link_sessions",
        ["retailer_offering_id"],
    )

    op.create_table(
        "purchase_targets",
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_offering_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_product_id", sa.String(length=160), nullable=False),
        sa.Column("retailer_variant_id", sa.String(length=160), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=300), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customer_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["retailer_offering_id"], ["retailer_offerings.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_purchase_targets_customer_id", "purchase_targets", ["customer_id"]
    )
    op.create_index(
        "ix_purchase_targets_retailer_offering_id",
        "purchase_targets",
        ["retailer_offering_id"],
    )
    op.create_index(
        "ix_target_identity",
        "purchase_targets",
        [
            "customer_id",
            "retailer_offering_id",
            "retailer_product_id",
            "retailer_variant_id",
        ],
    )

    op.create_table(
        "monitoring_jobs",
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("entitlement_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_profile_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_target_id", sa.Uuid(), nullable=False),
        sa.Column(
            "workflow_mode",
            sa.Enum(
                "DRY_RUN",
                "ASSISTED_CHECKOUT",
                "AUTO_PURCHASE",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("max_unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("quantity_requested", sa.Integer(), nullable=False),
        sa.Column("success_limit", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "CREATED",
                "PREFLIGHT",
                "READY",
                "QUEUED",
                "MONITORING",
                "ITEM_FOUND",
                "VALIDATING",
                "ADDING_TO_CART",
                "CART_CONFIRMED",
                "CHECKOUT_PREPARING",
                "CHECKOUT_READY",
                "AWAITING_CONFIRMATION",
                "PURCHASE_AUTHORIZED",
                "SUBMITTING",
                "ORDER_CONFIRMED",
                "COMPLETED",
                "PAUSED",
                "ACTION_REQUIRED",
                "FAILED",
                "EXPIRED",
                "STOPPED",
                "AMBIGUOUS",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("max_unit_price > 0"),
        sa.CheckConstraint("quantity_requested > 0"),
        sa.CheckConstraint("success_limit > 0"),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customer_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["entitlement_id"], ["service_entitlements.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["purchase_target_id"], ["purchase_targets.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["retailer_profile_id"], ["retailer_profiles.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_jobs_customer_status",
        "monitoring_jobs",
        ["customer_id", "status"],
    )
    op.create_index(
        "ix_monitoring_jobs_customer_id", "monitoring_jobs", ["customer_id"]
    )
    op.create_index(
        "ix_monitoring_jobs_entitlement_id", "monitoring_jobs", ["entitlement_id"]
    )
    op.create_index(
        "ix_monitoring_jobs_expires_at", "monitoring_jobs", ["expires_at"]
    )
    op.create_index(
        "ix_monitoring_jobs_purchase_target_id",
        "monitoring_jobs",
        ["purchase_target_id"],
    )
    op.create_index(
        "ix_monitoring_jobs_retailer_profile_id",
        "monitoring_jobs",
        ["retailer_profile_id"],
    )
    op.create_index("ix_monitoring_jobs_status", "monitoring_jobs", ["status"])

    op.create_table(
        "purchase_attempts",
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column(
            "state",
            sa.Enum(
                "CREATED",
                "RUNNING",
                "SUBMISSION_STARTED",
                "CONFIRMED",
                "REJECTED",
                "FAILED",
                "AMBIGUOUS",
                "RECONCILING",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("observed_unit_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("quantity_attempted", sa.Integer(), nullable=False),
        sa.Column("failure_code", sa.String(length=80), nullable=True),
        sa.Column("reference_id", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ambiguous_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"], ["monitoring_jobs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "attempt_number", name="uq_attempt_job_number"),
        sa.UniqueConstraint("reference_id"),
    )
    op.create_index(
        "ix_attempt_job_state", "purchase_attempts", ["job_id", "state"]
    )
    op.create_index("ix_purchase_attempts_job_id", "purchase_attempts", ["job_id"])

    op.create_table(
        "orders",
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_profile_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_attempt_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_order_reference", sa.String(length=200), nullable=False),
        sa.Column("quantity_confirmed", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("quantity_confirmed > 0"),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customer_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["monitoring_jobs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["purchase_attempt_id"], ["purchase_attempts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["retailer_profile_id"], ["retailer_profiles.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("purchase_attempt_id"),
        sa.UniqueConstraint(
            "retailer_profile_id",
            "retailer_order_reference",
            name="uq_order_retailer_profile_reference",
        ),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_index("ix_orders_job_id", "orders", ["job_id"])
    op.create_index(
        "ix_orders_retailer_profile_id", "orders", ["retailer_profile_id"]
    )

    op.create_table(
        "job_events",
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["purchase_attempts.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["monitoring_jobs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_job_events_job_created", "job_events", ["job_id", "created_at"]
    )
    op.create_index("ix_job_events_job_id", "job_events", ["job_id"])

    op.create_table(
        "worker_leases",
        sa.Column("worker_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_profile_id", sa.Uuid(), nullable=False),
        sa.Column("lease_token_hash", sa.String(length=128), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "RELEASED", "EXPIRED", "REVOKED", native_enum=False),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["retailer_profile_id"], ["retailer_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lease_token_hash"),
    )
    op.create_index(
        "ix_worker_lease_profile_status",
        "worker_leases",
        ["retailer_profile_id", "status"],
    )
    op.create_index(
        "ix_worker_leases_expires_at", "worker_leases", ["expires_at"]
    )
    op.create_index(
        "ix_worker_leases_retailer_profile_id",
        "worker_leases",
        ["retailer_profile_id"],
    )
    op.create_index("ix_worker_leases_status", "worker_leases", ["status"])
    op.create_index("ix_worker_leases_worker_id", "worker_leases", ["worker_id"])
    op.create_index(
        "uq_active_lease_per_profile",
        "worker_leases",
        ["retailer_profile_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    op.create_table(
        "retailer_health_snapshots",
        sa.Column("retailer_offering_id", sa.Uuid(), nullable=False),
        sa.Column(
            "health_state",
            sa.Enum(
                "HEALTHY", "DEGRADED", "OUTAGE", "MAINTENANCE", native_enum=False
            ),
            nullable=False,
        ),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["retailer_offering_id"], ["retailer_offerings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_retailer_health_observed",
        "retailer_health_snapshots",
        ["retailer_offering_id", "observed_at"],
    )
    op.create_index(
        "ix_retailer_health_snapshots_observed_at",
        "retailer_health_snapshots",
        ["observed_at"],
    )
    op.create_index(
        "ix_retailer_health_snapshots_retailer_offering_id",
        "retailer_health_snapshots",
        ["retailer_offering_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_retailer_health_snapshots_retailer_offering_id",
        table_name="retailer_health_snapshots",
    )
    op.drop_index(
        "ix_retailer_health_snapshots_observed_at",
        table_name="retailer_health_snapshots",
    )
    op.drop_index(
        "ix_retailer_health_observed",
        table_name="retailer_health_snapshots",
    )
    op.drop_table("retailer_health_snapshots")

    op.drop_index("uq_active_lease_per_profile", table_name="worker_leases")
    op.drop_index("ix_worker_leases_worker_id", table_name="worker_leases")
    op.drop_index("ix_worker_leases_status", table_name="worker_leases")
    op.drop_index(
        "ix_worker_leases_retailer_profile_id", table_name="worker_leases"
    )
    op.drop_index("ix_worker_leases_expires_at", table_name="worker_leases")
    op.drop_index("ix_worker_lease_profile_status", table_name="worker_leases")
    op.drop_table("worker_leases")

    op.drop_index("ix_job_events_job_id", table_name="job_events")
    op.drop_index("ix_job_events_job_created", table_name="job_events")
    op.drop_table("job_events")

    op.drop_index("ix_orders_retailer_profile_id", table_name="orders")
    op.drop_index("ix_orders_job_id", table_name="orders")
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_purchase_attempts_job_id", table_name="purchase_attempts")
    op.drop_index("ix_attempt_job_state", table_name="purchase_attempts")
    op.drop_table("purchase_attempts")

    op.drop_index("ix_monitoring_jobs_status", table_name="monitoring_jobs")
    op.drop_index(
        "ix_monitoring_jobs_retailer_profile_id", table_name="monitoring_jobs"
    )
    op.drop_index(
        "ix_monitoring_jobs_purchase_target_id", table_name="monitoring_jobs"
    )
    op.drop_index("ix_monitoring_jobs_expires_at", table_name="monitoring_jobs")
    op.drop_index("ix_monitoring_jobs_entitlement_id", table_name="monitoring_jobs")
    op.drop_index("ix_monitoring_jobs_customer_id", table_name="monitoring_jobs")
    op.drop_index("ix_jobs_customer_status", table_name="monitoring_jobs")
    op.drop_table("monitoring_jobs")

    op.drop_index("ix_target_identity", table_name="purchase_targets")
    op.drop_index(
        "ix_purchase_targets_retailer_offering_id", table_name="purchase_targets"
    )
    op.drop_index("ix_purchase_targets_customer_id", table_name="purchase_targets")
    op.drop_table("purchase_targets")

    op.drop_index(
        "ix_account_link_sessions_retailer_offering_id",
        table_name="account_link_sessions",
    )
    op.drop_index(
        "ix_account_link_sessions_expires_at", table_name="account_link_sessions"
    )
    op.drop_index(
        "ix_account_link_sessions_customer_id", table_name="account_link_sessions"
    )
    op.drop_table("account_link_sessions")

    op.drop_index("ix_retailer_profiles_status", table_name="retailer_profiles")
    op.drop_index(
        "ix_retailer_profiles_retailer_offering_id",
        table_name="retailer_profiles",
    )
    op.drop_index(
        "ix_retailer_profiles_customer_id", table_name="retailer_profiles"
    )
    op.drop_table("retailer_profiles")

    op.drop_index(
        "ix_service_entitlements_status", table_name="service_entitlements"
    )
    op.drop_index(
        "ix_service_entitlements_retailer_offering_id",
        table_name="service_entitlements",
    )
    op.drop_index(
        "ix_service_entitlements_customer_id",
        table_name="service_entitlements",
    )
    op.drop_index(
        "ix_entitlements_customer_retailer_status",
        table_name="service_entitlements",
    )
    op.drop_table("service_entitlements")

    op.drop_index(
        "ix_discord_identities_discord_user_id", table_name="discord_identities"
    )
    op.drop_index(
        "ix_discord_identities_customer_id", table_name="discord_identities"
    )
    op.drop_table("discord_identities")

    op.drop_index("ix_workers_status", table_name="workers")
    op.drop_index("ix_workers_last_heartbeat_at", table_name="workers")
    op.drop_table("workers")

    op.drop_index(
        "ix_retailer_offerings_retailer_code", table_name="retailer_offerings"
    )
    op.drop_table("retailer_offerings")

    op.drop_index("ix_customer_accounts_email", table_name="customer_accounts")
    op.drop_table("customer_accounts")

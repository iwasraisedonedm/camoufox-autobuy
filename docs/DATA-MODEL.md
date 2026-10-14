# Data Model

## Authority

PostgreSQL is the authoritative store for durable business state. Redis must never be required to reconstruct customer, entitlement, job, attempt, order, or allowance truth.

## Conventions

- Primary keys: UUID.
- Timestamps: UTC, timezone-aware.
- Money: fixed-precision decimal plus currency code.
- External IDs: stored separately from internal UUIDs.
- Soft deletion only where audit/history requires it.
- Sensitive retailer session material is not stored directly in relational rows; store encrypted artifact references.
- State transitions that affect purchasing or allowance must be transactional.

## Entities

### CustomerAccount

Represents the canonical service-owned customer identity.

Key fields:

- `id`
- `email` unique, normalized
- `status`
- `created_at`
- `updated_at`
- `disabled_at`

Relations:

- one-to-many DiscordIdentity
- one-to-many ServiceEntitlement
- one-to-many RetailerProfile
- one-to-many PurchaseTarget
- one-to-many MonitoringJob

### DiscordIdentity

Links Discord to CustomerAccount.

Fields:

- `id`
- `customer_id`
- `discord_user_id` unique
- `linked_at`
- `revoked_at`

Discord is not the canonical customer identity.

### RetailerOffering

Defines one sellable supported retailer capability.

Fields:

- `id`
- `retailer_code`
- `display_name`
- `status`
- `adapter_version`
- `created_at`
- `updated_at`

Retailer codes are stable machine identifiers such as `bestbuy`.

### ServiceEntitlement

Represents purchased authorization to use one retailer offering under bounded limits.

Fields:

- `id`
- `customer_id`
- `retailer_offering_id`
- `starts_at`
- `expires_at`
- `concurrent_job_limit`
- `successful_unit_allowance_total`
- `successful_unit_allowance_used`
- `status`
- `external_grant_reference`
- `created_at`

Invariant:

`successful_unit_allowance_used <= successful_unit_allowance_total`.

A new attempt may not begin when expired or exhausted.

### RetailerProfile

Represents one customer retailer account/session identity.

Fields:

- `id`
- `customer_id`
- `retailer_offering_id`
- `label`
- `status`
- `encrypted_artifact_ref`
- `artifact_version`
- `last_authenticated_at`
- `last_verified_at`
- `created_at`
- `updated_at`

V1 UI exposes one profile per customer/retailer, but schema permits multiple profiles.

### AccountLinkSession

Short-lived record for retailer account linking.

Fields:

- `id`
- `customer_id`
- `retailer_offering_id`
- `token_hash`
- `expires_at`
- `status`
- `created_at`
- `completed_at`

Never store reusable retailer credentials in this record.

### PurchaseTarget

Reusable item definition.

Fields:

- `id`
- `customer_id`
- `retailer_offering_id`
- `retailer_product_id`
- `retailer_variant_id`
- `url`
- `display_name`
- `created_at`
- `updated_at`

Target identity is retailer + retailer product ID + optional variant.

### MonitoringJob

One execution lifecycle against one target.

Fields:

- `id`
- `customer_id`
- `entitlement_id`
- `retailer_profile_id`
- `purchase_target_id`
- `workflow_mode`
- `max_unit_price`
- `currency`
- `quantity_requested`
- `success_limit`
- `expires_at`
- `status`
- `created_at`
- `started_at`
- `completed_at`
- `version`

Constraints are copied into the job when created.

### PurchaseAttempt

Represents one attempt to progress a job toward checkout.

Fields:

- `id`
- `job_id`
- `attempt_number`
- `state`
- `observed_unit_price`
- `currency`
- `quantity_attempted`
- `failure_code`
- `reference_id`
- `started_at`
- `finished_at`
- `ambiguous_at`

Unique: `job_id + attempt_number`.

### Order

Durable confirmed purchase outcome.

Fields:

- `id`
- `customer_id`
- `job_id`
- `purchase_attempt_id`
- `retailer_order_reference`
- `quantity_confirmed`
- `unit_price`
- `currency`
- `confirmed_at`
- `created_at`

Unique retailer order reference per retailer profile where supported.

Allowance decrement and Order creation must occur in one transaction.

### JobEvent

Append-only meaningful job event.

Fields:

- `id`
- `job_id`
- `attempt_id`
- `event_type`
- `payload_json`
- `created_at`

Payload must be sanitized and contain no secrets.

### Worker

Ephemeral execution node identity.

Fields:

- `id`
- `instance_id`
- `status`
- `version`
- `last_heartbeat_at`
- `started_at`

### WorkerLease

Renewable ownership record binding a worker to a retailer runtime/job set.

Fields:

- `id`
- `worker_id`
- `retailer_profile_id`
- `lease_token_hash`
- `acquired_at`
- `expires_at`
- `released_at`
- `status`

Invariant: at most one active lease per retailer profile.

### RetailerHealthSnapshot

Stores summarized retailer health observations.

Fields:

- `id`
- `retailer_offering_id`
- `health_state`
- `metrics_json`
- `observed_at`

## Transaction boundaries

The following must be atomic:

- creating a job and reserving entitlement concurrency
- confirmed order creation and successful-unit allowance decrement
- stopping/completing a job and releasing durable concurrency accounting
- resolving an ambiguous attempt
- disconnecting a retailer profile and invalidating active jobs

## Indexes

At minimum index:

- customer foreign keys
- active entitlements by customer/retailer
- active jobs by customer/retailer/status
- attempts by job/state
- orders by customer/retailer reference
- active leases by retailer profile
- retailer health by retailer/time

## Migration policy

Use Alembic from the first production schema. Never modify production tables outside migrations.

"""Canonical domain state values."""

from enum import StrEnum


class CustomerStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class EntitlementStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RetailerProfileStatus(StrEnum):
    DISCONNECTED = "disconnected"
    LINK_PENDING = "link_pending"
    AUTHENTICATED = "authenticated"
    READY = "ready"
    REAUTH_REQUIRED = "reauth_required"
    LOCKED = "locked"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


class WorkflowMode(StrEnum):
    DRY_RUN = "dry_run"
    ASSISTED_CHECKOUT = "assisted_checkout"
    AUTO_PURCHASE = "auto_purchase"


class JobStatus(StrEnum):
    CREATED = "created"
    PREFLIGHT = "preflight"
    READY = "ready"
    QUEUED = "queued"
    MONITORING = "monitoring"
    ITEM_FOUND = "item_found"
    VALIDATING = "validating"
    ADDING_TO_CART = "adding_to_cart"
    CART_CONFIRMED = "cart_confirmed"
    CHECKOUT_PREPARING = "checkout_preparing"
    CHECKOUT_READY = "checkout_ready"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    PURCHASE_AUTHORIZED = "purchase_authorized"
    SUBMITTING = "submitting"
    ORDER_CONFIRMED = "order_confirmed"
    COMPLETED = "completed"
    PAUSED = "paused"
    ACTION_REQUIRED = "action_required"
    FAILED = "failed"
    EXPIRED = "expired"
    STOPPED = "stopped"
    AMBIGUOUS = "ambiguous"


class AttemptStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    SUBMISSION_STARTED = "submission_started"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"
    RECONCILING = "reconciling"


class WorkerStatus(StrEnum):
    STARTING = "starting"
    REGISTERED = "registered"
    IDLE = "idle"
    LEASED = "leased"
    RUNNING = "running"
    DRAINING = "draining"
    STOPPED = "stopped"
    LOST = "lost"


class LeaseStatus(StrEnum):
    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RetailerHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OUTAGE = "outage"
    MAINTENANCE = "maintenance"

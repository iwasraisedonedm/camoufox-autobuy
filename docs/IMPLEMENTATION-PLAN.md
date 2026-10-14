# Implementation Plan

## Purpose

This document is the authoritative build order for AutoBuy v1. It translates the accepted architecture into implementation phases. Agents must preserve dependency order unless a documented technical dependency requires deviation.

## Current implementation status

- Phase 0 — complete
- Phase 1 — complete foundation
- Phase 2 — substantially implemented; remaining lifecycle/admin endpoints continue incrementally
- Phase 3 — pending
- Phase 4 — core entitlement accounting implemented
- Phase 5 — Redis coordination, queues, worker registration, heartbeats, renewable leases, stale-lease recovery, and safe reassignment implemented
- Phase 6 — encrypted retailer-profile artifact foundation implemented; production object-store/KMS adapters remain
- Phase 7+ — pending

## Delivery principles

- Build one production-quality vertical slice before broadening scope.
- Best Buy is the reference retailer.
- PostgreSQL is authoritative; Redis is reconstructable coordination state.
- Discord is an interface, not the source of truth.
- Customer retailer profiles are encrypted and isolated.
- Live purchase submission is never exercised by CI.
- Ambiguous purchase outcomes block automatic resubmission.
- Architecture changes require documentation and, where appropriate, an ADR.

## Phase 0 — Repository and tooling baseline

Deliver:

- Python 3.12+ project layout
- uv lockfile
- Ruff
- Pyright
- pytest / pytest-asyncio / pytest-cov
- GitHub Actions
- pre-commit-compatible validation commands
- structured settings loading
- production-safe logging foundation

Exit criteria:

- clean checkout installs reproducibly
- lint, format, typecheck, and tests pass
- CI requires no secrets
- no live browser purchase flow runs in CI

## Phase 1 — Domain and persistence

Implement the domain defined in `CONTEXT.md` and `DATA-MODEL.md`.

Deliver:

- PostgreSQL integration
- SQLAlchemy async models
- Alembic migrations
- repository interfaces
- transactional unit-of-work boundary
- customer accounts
- Discord identities
- retailer offerings
- entitlements
- retailer profiles
- purchase targets
- monitoring jobs
- purchase attempts
- orders
- job events
- worker leases

Exit criteria:

- schema is migration-driven
- domain constraints are database-enforced where practical
- entitlement decrement is transactional
- duplicate purchase protection has durable backing

## Phase 2 — Control plane API

Deliver:

- FastAPI application
- versioned internal API
- request IDs
- structured error envelope
- internal service authentication
- customer lookup
- entitlement validation
- target/job creation
- job stop/pause/status endpoints
- worker lease endpoints
- profile metadata endpoints
- health/readiness endpoints

Exit criteria:

- all writes pass through application services
- clients do not write PostgreSQL directly
- idempotency implemented for sensitive mutation endpoints
- OpenAPI schema generated and testable

## Phase 3 — Discord interface

Deliver:

- linked Discord identity resolution
- slash commands
- guided `/autobuy` flow
- `/shop`
- `/connect`
- `/status`
- `/stop`
- `/disconnect`
- persistent job status cards
- terminal-event notifications
- admin commands

Exit criteria:

- Discord contains no authoritative business state
- every command is authorized through the control plane
- customer-facing errors expose reference IDs, not internals

## Phase 4 — Entitlement integration

Deliver:

- private entitlement-grant API
- signed/internal authentication
- duration limits
- concurrent-job limits
- successful-unit allowance
- entitlement exhaustion
- entitlement audit records

Exit criteria:

- separate unlock service can grant entitlements without DB access
- failed purchases do not consume allowance
- confirmed units consume allowance transactionally

## Phase 5 — Redis coordination and worker orchestration

Deliver:

- retailer-specific queues
- worker registration
- renewable leases
- heartbeats
- lease expiry
- profile/runtime locks
- rate-limit counters
- worker re-assignment
- safe recovery policy

Exit criteria:

- Redis loss does not lose authoritative state
- zombie leases expire
- only one active writer may own a retailer profile

## Phase 6 — Secure retailer profile storage

Deliver:

- object-storage abstraction
- encrypted profile artifact model
- envelope-encryption provider interface
- local dev provider
- production KMS/secrets-manager provider
- upload/download lifecycle
- ephemeral worker restoration
- secure teardown

Exit criteria:

- plaintext profiles are never committed or persisted outside active workers
- control plane does not routinely decrypt profile artifacts
- profile writes are single-writer protected

## Phase 7 — Worker runtime

Deliver:

- generic worker process
- retailer adapter registry
- retailer transport abstraction
- browser automation transport
- supported structured retailer transport where appropriate
- Chromium persistent context
- runtime health
- structured worker events
- safe restart behavior
- job state persistence

Exit criteria:

- workers can restore a profile, run monitoring, checkpoint state, and shut down cleanly
- worker loss in safe states is recoverable

## Phase 8 — Best Buy adapter and transport validation

Transport validation should compare supported implementation options behind the same normalized adapter contract. Monitoring and checkout may use different transports. Selection should be based on measured reliability, latency, session stability, and operational simplicity.

Deliver according to `RETAILER-ADAPTER-SPEC.md`:

- session status
- product normalization
- availability
- price
- variant
- cart
- checkout preparation
- final submission contract
- confirmation parsing
- order reconciliation
- adapter health

Exit criteria:

- fixture-driven tests
- dry-run integration tests
- no retailer-specific selectors outside adapter package

## Phase 9 — End-to-end product flow

Validate:

```text
Customer
→ Discord
→ Entitlement
→ Best Buy connect
→ Purchase target
→ Monitoring job
→ Worker lease
→ Product available
→ Guards
→ Cart
→ Checkout
→ Purchase submission
→ Confirmation
→ Allowance decrement
→ Discord success
```

Exit criteria:

- duplicate prevention proven
- ambiguous outcome path proven
- worker failure recovery proven
- account reauthentication path proven

## Phase 10 — Production hardening

Deliver:

- production secrets manager
- backup procedures
- metrics and alerts
- retailer health state
- log redaction review
- outbound worker network policy
- retention policy
- restore drill
- load test
- incident runbooks
- operator documentation

## Release gate

V1 is releasable only when `docs/V1-ACCEPTANCE.md` and `docs/DEFINITION-OF-DONE.md` are satisfied.

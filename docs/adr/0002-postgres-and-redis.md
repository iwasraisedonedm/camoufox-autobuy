# ADR 0002: PostgreSQL as System of Record and Redis for Ephemeral Coordination

## Status

Accepted.

## Context

SQLite was suitable for the original single-machine concept but does not fit the commercial multi-customer architecture. The system also needs fast ephemeral coordination for worker leases, queues, heartbeats, locks, and rate limits.

Using Redis as authoritative storage would risk losing durable customer and purchase state.

## Decision

Use PostgreSQL as the authoritative system of record.

Use Redis only for ephemeral coordination, including:

- retailer queues
- worker heartbeats
- renewable leases
- short-lived locks
- rate-limit counters
- event/status fan-out

The system must remain recoverable if Redis is cleared or restarted.

## Consequences

Positive:

- durable relational customer/job/entitlement state
- transactional allowance accounting
- reconstructable coordination layer
- clean separation between durable truth and transient execution state

Costs:

- two stateful infrastructure services
- explicit reconciliation between queue state and durable job state

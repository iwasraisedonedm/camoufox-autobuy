# ADR 0001: Separate Control Plane and Worker Plane

## Status

Accepted.

## Context

The original repository was conceived as a local browser automation utility. The product direction changed to a hosted commercial Discord service serving multiple customers, each with isolated retailer sessions and active purchase jobs.

A single monolithic process would couple customer/entitlement state to unstable browser workloads. Full microservices would add unnecessary operational complexity.

## Decision

Use two primary execution planes:

- a central control plane for authoritative business state, Discord/API actions, entitlements, job orchestration, and operator actions
- an isolated worker plane for retailer browser automation

Workers receive renewable leases and execute jobs without becoming the source of truth.

## Consequences

Positive:

- browser crashes are isolated from business-state services
- workers scale independently
- customer jobs can recover after worker loss
- retailer-specific capacity can be managed separately
- source code remains server-side

Costs:

- requires queue/lease protocol
- requires durable job state
- requires profile handoff/storage
- requires more deployment components than a local application

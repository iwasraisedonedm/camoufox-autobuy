# ADR 0004: Transport-Agnostic Retailer Adapters

## Status

Accepted.

## Context

The initial worker design emphasized browser automation. The platform now needs retailer adapters that can choose among supported implementation mechanisms without forcing the rest of the system to depend on one transport.

## Decision

Retailer adapters expose one normalized contract and select transport internally per operation.

Supported transport categories are browser automation and retailer-supported structured integrations. Monitoring and checkout may use different transports.

The control plane, Discord layer, domain model, and persistence model remain transport-independent.

## Consequences

Benefits:

- retailer-specific optimization without platform redesign
- browser compatibility remains available
- transport choices can be based on measured reliability and latency

Costs:

- more adapter-level testing
- transport-aware observability
- explicit fallback behavior
- additional session-state handling

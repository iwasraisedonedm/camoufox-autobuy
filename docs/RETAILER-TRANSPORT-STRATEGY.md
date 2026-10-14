# Retailer Transport Strategy

## Purpose

Retailer adapters may use more than one supported implementation mechanism while exposing one stable contract to the rest of AutoBuy.

## Core rule

Choose the implementation mechanism for each retailer operation based on measured reliability, compatibility, latency, and maintainability.

## Supported categories

A retailer adapter may use:

- browser automation
- a retailer-supported structured integration
- a combination of both

Monitoring and checkout may use different mechanisms.

## Architectural boundary

Transport details remain inside retailer adapters and worker runtime. Discord, the control plane, persistence, entitlements, and customer-facing states remain transport-independent.

## Runtime preparation

A retailer runtime should prepare reusable authenticated state, product identity, selected variant, and configuration before active execution when practical.

## Validation

For each supported transport, measure:

- operation success rate
- latency
- session stability
- error rate
- fallback rate

The default implementation should be selected from evidence rather than convention.

## Safety and compatibility

Transport changes must not alter authorization, customer ownership, purchase guards, idempotency, state transitions, or reconciliation rules.

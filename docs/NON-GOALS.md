# Non-Goals

## Purpose

This file prevents scope creep and architecture drift.

Items below are intentionally outside v1 unless explicitly promoted through a product decision.

## V1 non-goals

- Telegram support
- arbitrary unsupported websites
- generic universal checkout automation
- customer-facing multiple retailer accounts per retailer
- cross-retailer substitute-product matching
- AI deciding what the customer should purchase
- customer-controlled polling frequency
- public developer API
- customer web dashboard
- customer mobile app
- Kubernetes
- multi-region deployment
- distributed microservice sprawl
- per-customer virtual machines
- Redis as system of record
- storing raw payment-card data
- collecting retailer passwords through Discord
- using Discord roles/messages as entitlement truth
- direct unlock-service database writes
- uncontrolled browser-profile sharing
- generic automatic retries around final submission
- bypassing explicit human verification/access-control steps

## Architectural non-goals

Do not optimize for:

- minimum possible RAM at the expense of reliability
- clever abstractions before a second real use case exists
- supporting every browser engine
- replacing PostgreSQL with an event store
- premature multi-cloud portability
- premature service decomposition

## Product positioning

The initial product is a curated supported-retailer AutoBuy service, not a general browser automation marketplace.

Best Buy is the reference retailer. Future retailers are added deliberately based on commercial demand and technical readiness.

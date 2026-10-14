# AutoBuy

AutoBuy is a hosted commercial purchasing platform that monitors explicitly supported retailers and executes authorized purchase workflows for customers through a Discord-first interface.

Best Buy is the initial reference retailer.

> Status: architecture and production specifications are established. Core application implementation is the next phase.

## Product direction

Customers:

- create/link a service account
- purchase a retailer-specific entitlement
- connect their retailer account through a secure hosted account-link session
- configure a purchase target
- start an Auto Purchase job from Discord
- receive live status updates and a confirmed outcome

The source code and browser automation infrastructure remain server-side.

Auto Purchase is the defining commercial capability. Dry-run and assisted checkout remain supporting modes.

## High-level architecture

```text
Customer
   |
Discord
   |
Control Plane API
   |
   +-- PostgreSQL
   +-- Redis
   +-- Encrypted Retailer Profile Storage
   |
Worker Orchestrator
   |
Retailer Queue
   |
Isolated Worker Runtime
   |
Patchright + Chromium
   |
Supported Retailer
```

See `ARCHITECTURE.md` for the complete system design.

## Core architecture decisions

- PostgreSQL is durable truth.
- Redis is ephemeral coordination.
- Discord is an interface, not a database.
- Control plane and worker plane are separated.
- Customer retailer profiles are isolated and encrypted.
- One active writer owns a retailer profile at a time.
- Workers are disposable.
- Final purchase submission is not blindly retried.
- Ambiguous outcomes require reconciliation.
- CI never performs live purchases.

## Documentation

Start with:

- `AGENTS.md` — agent operating rules
- `CONTEXT.md` — domain vocabulary
- `ARCHITECTURE.md` — system architecture
- `docs/README.md` — documentation authority map
- `docs/IMPLEMENTATION-PLAN.md` — build order
- `docs/V1-ACCEPTANCE.md` — v1 release bar

Subsystem specifications live under `docs/`.

## Production stack

Control plane:

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Redis
- Pydantic
- Discord API/client
- structlog

Worker plane:

- Python 3.12+
- asyncio
- Patchright
- Chromium
- retailer adapters
- encrypted retailer profile storage

Development:

- uv
- Alembic
- pytest
- Ruff
- Pyright
- GitHub Actions

## Commercial model

A Service Entitlement may meter:

- supported retailer
- duration
- concurrent monitored products/jobs
- confirmed successful unit allowance

Failed attempts do not consume successful-purchase allowance.

The separate unlock/payment service grants entitlements through a private authenticated API.

## V1

V1 is Best Buy-first and includes:

- customer identity + Discord linking
- retailer entitlements
- Best Buy account linking
- encrypted persistent retailer session/profile
- product monitoring
- exact SKU/variant validation
- max-price and quantity guards
- isolated worker runtime
- automatic cart/checkout/submission
- confirmed order detection
- duplicate prevention
- ambiguous-outcome reconciliation
- status cards and notifications
- worker failure recovery
- operator controls
- observability
- tests and CI

See `docs/V1-ACCEPTANCE.md` for the authoritative acceptance criteria.

## Scope boundaries

AutoBuy supports a curated set of explicitly implemented retailers.

V1 does not include arbitrary websites, Telegram, a customer web dashboard, customer-controlled polling frequency, cross-retailer substitutes, Kubernetes, or multi-region deployment.

When a retailer requires explicit human verification or access-control interaction, AutoBuy pauses and asks the customer to complete that action rather than attempting to defeat the control.

## Implementation

Follow `docs/IMPLEMENTATION-PLAN.md`.

Do not start by building multiple retailer adapters. Best Buy must first become a complete production-quality reference implementation.

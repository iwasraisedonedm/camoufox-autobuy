# Observability

## Purpose

Observability exists to answer, quickly and without exposing secrets:

- Is the platform healthy?
- Is a retailer healthy?
- Is a customer's job progressing?
- Where is latency accumulating?
- Did a purchase succeed, fail, or become ambiguous?
- Which worker handled the attempt?
- Can an operator trace the complete lifecycle from Discord command to retailer outcome?

## Correlation model

Every customer-visible operation should carry a correlation chain.

Required identifiers where applicable:

- `request_id`
- `customer_id`
- `discord_interaction_id`
- `entitlement_id`
- `retailer_profile_id`
- `purchase_target_id`
- `job_id`
- `attempt_id`
- `worker_id`
- `lease_id`
- `order_id`
- `reference_id`

Never use email addresses, Discord display names, or retailer usernames as log correlation keys.

## Structured logs

Use structured JSON logs in production.

Minimum fields:

- timestamp
- level
- service
- environment
- event
- request_id
- correlation_id
- resource IDs relevant to the event
- duration_ms when applicable
- result/status
- error_code when applicable

Do not log:

- passwords
- cookies
- authorization headers
- session storage
- browser local storage
- card data
- account-link tokens
- encryption keys
- full customer addresses
- raw sensitive HTML forms

## Canonical events

Control plane:

- `CUSTOMER_CREATED`
- `DISCORD_LINKED`
- `ENTITLEMENT_GRANTED`
- `ENTITLEMENT_EXHAUSTED`
- `JOB_CREATED`
- `JOB_STARTED`
- `JOB_PAUSED`
- `JOB_STOPPED`
- `JOB_EXPIRED`

Retailer profile:

- `ACCOUNT_LINK_STARTED`
- `ACCOUNT_LINK_COMPLETED`
- `PROFILE_AUTHENTICATED`
- `PROFILE_REAUTH_REQUIRED`
- `PROFILE_DISCONNECTED`

Worker:

- `WORKER_REGISTERED`
- `LEASE_ACQUIRED`
- `LEASE_RENEWED`
- `LEASE_EXPIRED`
- `PROFILE_RESTORED`
- `PROFILE_CHECKPOINTED`
- `WORKER_LOST`

Purchase flow:

- `MONITORING_STARTED`
- `PRODUCT_OBSERVED`
- `PRODUCT_AVAILABLE`
- `GUARDS_PASSED`
- `GUARD_REJECTED`
- `ADD_TO_CART_STARTED`
- `CART_CONFIRMED`
- `CHECKOUT_READY`
- `SUBMISSION_STARTED`
- `ORDER_CONFIRMED`
- `SUBMISSION_AMBIGUOUS`
- `PURCHASE_FAILED`

## Metrics

### Platform

- active customers
- active entitlements
- active jobs
- queued jobs
- active workers
- worker capacity
- queue wait time
- API request latency/error rate
- DB connection saturation
- Redis availability

### Retailer

- product-check success rate
- session-validation success rate
- cart success rate
- checkout-preparation success rate
- confirmed automation success rate
- reauthentication rate
- ambiguous-submission rate
- median/p95 monitoring latency
- median/p95 checkout latency
- transport selected per retailer operation
- per-transport success/error rate

### Worker

- worker heartbeat age
- lease renewal failures
- profile restore duration
- browser startup duration
- crash/restart rate
- memory/CPU utilization
- active runtime count

## Retailer health state

Compute one operational state per supported retailer:

- `HEALTHY`
- `DEGRADED`
- `OUTAGE`
- `MAINTENANCE`

Health is based on aggregate signals, not a single customer failure.

## Alerts

Initial high-priority alerts:

- PostgreSQL unavailable
- Redis unavailable
- object storage unavailable
- KMS/secrets provider unavailable
- retailer success-rate collapse
- ambiguous purchase
- worker fleet capacity exhausted
- repeated profile restore/checkpoint failures
- elevated reauthentication rate
- internal API authentication failures
- entitlement accounting mismatch

Route v1 operator alerts to a private Discord admin channel and durable logs.

## Reliability target

A supported retailer adapter should demonstrate at least 95% successful execution of platform-controlled automation steps under normal supported-retailer conditions before production release.

This does not imply guaranteed stock availability, payment approval, or retailer acceptance.

## Retention

- application logs: bounded operational retention
- audit events: longer retention
- screenshots/traces: short retention
- metrics: sufficient retention to compare releases and retailer regressions

Exact durations must be documented before public launch.

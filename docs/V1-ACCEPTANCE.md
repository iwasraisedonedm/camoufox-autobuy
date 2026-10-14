# V1 Acceptance Criteria

V1 is the first sellable AutoBuy product, not an internal monitoring demo.

## Commercial capability

The defining acceptance criterion is a confirmed successful automatic purchase on Best Buy using a customer's authenticated retailer session, subject to configured guards and entitlement limits.

## Required customer capabilities

- create/link a customer account
- link Discord identity
- purchase/unlock a Best Buy service entitlement through the separate unlock service
- connect a Best Buy account through a secure hosted account-link session
- create a purchase target
- start an Auto Purchase monitoring job
- inspect job status
- stop a job
- disconnect the retailer profile
- receive action-required, failure, and success notifications

## Required entitlement behavior

- retailer-specific entitlement
- time window
- concurrent monitored-product limit
- successful unit allowance
- failed attempts do not consume successful unit allowance
- confirmed units consume allowance
- time expiry or exhausted allowance prevents new attempts
- an already-valid checkout may finish once after time expiry

## Required automation behavior

- persistent authenticated Best Buy profile
- warm retailer runtime
- exact SKU/product validation
- variant validation
- quantity validation
- maximum-price validation
- duplicate protection
- monitoring
- availability detection
- add to cart
- checkout preparation
- automatic final submission
- confirmed-order detection
- durable purchase outcome

## Required failure behavior

- explicit failure reason categories
- reauthentication pauses jobs and requests customer action
- worker failure safely resumes monitoring when possible
- ambiguous final submission blocks automatic resubmission
- ambiguous outcome is reconciled before another purchase
- errors exposed to customers use friendly text plus reference ID

## Required platform behavior

- FastAPI control plane
- PostgreSQL durable truth
- Redis ephemeral coordination
- retailer-specific queue
- renewable worker leases
- isolated worker containers
- encrypted retailer profiles in object storage
- production secret provider
- structured logging
- operator alerts
- retailer health state
- metrics for latency, success, failures, queueing, and workers

## Required Discord behavior

- `/shop`
- `/connect bestbuy`
- `/autobuy`
- `/status`
- `/stop`
- `/disconnect bestbuy`
- persistent editable job status card
- dedicated terminal-event notifications
- private customer interaction surface

## Production quality

A Best Buy adapter is not production-ready until normal-condition automation execution reaches at least the initial 95% reliability target in controlled testing.

CI must never execute live purchases.

## Explicitly out of scope

- Telegram
- arbitrary unsupported websites
- customer-controlled monitoring frequency
- cross-retailer substitutes
- customer-facing multi-account retailer UI
- customer web/mobile dashboard
- public API
- Kubernetes
- multi-region deployment
- AI purchase decisions

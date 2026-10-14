# Pricing and Entitlement Model

## Purpose

This document defines commercial mechanics, not final public prices.

Code must implement generic entitlement primitives so product packages can change without schema redesign.

## Commercial dimensions

A retailer package may define:

- supported retailer
- activation/start time
- duration
- concurrent monitored-product/job limit
- successful unit allowance

These are independent dimensions.

## Example package shapes

Illustrative only:

```text
Best Buy Day Pass
- 24 hours
- 1 concurrent job
- 1 successful unit

Best Buy Weekend
- 72 hours
- 3 concurrent jobs
- 3 successful units

Best Buy Monthly
- 30 days
- 5 concurrent jobs
- 10 successful units
```

Final names/prices are not architecture.

## Entitlement activation

Entitlements are granted by the separate unlock/payment service through authenticated internal API.

Required grant inputs:

- customer ID
- retailer offering
- starts_at
- expires_at
- concurrent_job_limit
- successful_unit_allowance_total
- external grant reference

Grant must be idempotent.

## Validity

An entitlement is usable only when:

- status is ACTIVE
- current time is inside the entitlement window
- successful allowance remains
- retailer offering is enabled

## Usage accounting

Failed attempts do not consume successful-unit allowance.

Confirmed purchased units do.

Example:

- requested quantity: 3
- confirmed quantity: 2
- allowance consumed: 2

Order creation and allowance decrement must be transactional.

## Concurrency

Concurrent-job limit controls how many Purchase Targets may actively monitor under the entitlement.

Concurrency is separate from purchase allowance.

## Expiration

After expiration:

- no new purchase attempt begins
- an already-valid in-progress checkout may complete once
- monitoring stops when current allowed in-progress work is resolved

## Exhaustion

When successful-unit allowance reaches zero:

- entitlement becomes EXHAUSTED
- no new purchase attempt begins
- remaining monitoring jobs stop or become inactive according to job policy

## Revocation

Authorized internal/operator action may revoke an entitlement.

Revocation:

- prevents new attempts
- pauses/stops affected jobs
- is auditable

## Refund/cancellation semantics

Commercial refund policy is not yet fixed.

Implementation must not infer financial refund behavior from entitlement revocation.

Keep payment/refund accounting in the unlock/payment service.

## Retailer separation

A Best Buy entitlement does not authorize Target unless explicitly represented by a separate entitlement/package.

## Product strategy

One technical platform may expose separate retailer-branded commercial offerings.

# ADR 0001 — Camoufox browser-first worker execution

Status: Accepted for staged implementation (not a production retailer release)

## Context

The existing hosted Discord-first AutoBuy architecture uses isolated retailer
workers and previously specified Patchright + Chromium as the browser runtime.
The project currently has no verified, authorized retailer checkout API to
justify a direct-HTTP purchase implementation.

## Decision

1. Prefer Camoufox + Playwright async for browser-driven retailer work.
2. Keep a normalized retailer adapter contract. Only workers/adapters know the
   browser implementation; Discord, entitlements and the control plane do not.
3. Continue PostgreSQL as durable truth, Redis as ephemeral coordination, and
   encrypted per-customer RetailerProfile artifacts with renewable exclusive
   worker leases. Do not adopt local SQLite or globally shared browser profiles.
4. Use one persistent Camoufox context per exclusively leased RetailerProfile
   in an ephemeral private directory. Restore only after lease validation;
   encrypt and checkpoint before lease release; destroy plaintext afterwards.
5. Monitoring uses browser page state/events and bounded, retailer-compliant
   refreshes. Do not use undocumented checkout endpoints or defeat verification,
   queues, rate limits, or purchase controls.
6. Retain Patchright during a staged transition. Do not switch the live Best Buy
   adapter until browser smoke tests, profile lifecycle tests, and fixture-based
   regression checks demonstrate compatibility.
7. Continue to guard purchases before final submission. Unknown outcomes stay
   AMBIGUOUS and are reconciled, never blindly resubmitted.

## Consequences

- Camoufox runtime becomes available to workers without changing domain/API contracts.
- Browser processes incur greater memory and startup cost than HTTP clients.
- Persistent Firefox context compatibility, worker image dependencies, binary
  provisioning, profile restore/checkpoint, and target-site behavior require
  explicit integration validation.
- Camoufox's stealth claims are not treated as guarantees of access.

## Rollout

1. Add worker runtime and unit tests; keep production adapter unchanged.
2. Add a staging-only smoke test and Docker image with a pinned Camoufox binary.
3. Integrate exclusive lease/profile-store lifecycle and runtime health events.
4. Implement/adapt a controlled demo retailer and fixture-based flow tests.
5. Trial Best Buy browser adapter only after authorization/compatibility review.
6. Remove Patchright only after no references remain and regression gates pass.

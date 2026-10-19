# ADR 0001 — Camoufox-first browser execution

Status: Proposed for staged rollout
Date: 2026-10-19

## Context

AutoBuy already has an accepted hosted Discord-first architecture with PostgreSQL, Redis, isolated customer retailer workers, leases, encrypted profiles, and normalized retailer adapters. Its current browser design specifies Patchright/Chromium. There is no confirmed authorized retailer checkout API to use as a default execution path.

## Decision

- Adopt Camoufox + Playwright as the **preferred browser runtime for new retailer adapter work**, behind the existing worker/adapter boundaries.
- Use browser navigation, DOM observations, and documented Playwright operations as the primary retailer interaction path.
- Retain the present Patchright path until Camoufox smoke tests, profile checkpoint/restore tests, and adapter parity testing pass. Do not replace the live worker by simply changing imports.
- Keep HTTPX for platform APIs, Discord integration, and independently permitted public/partner endpoints; do not require an HTTP purchasing transport.
- Preserve all currently accepted customer isolation, single-writer leases, encrypted-profile handling, purchase guards, idempotency, and AMBIGUOUS reconciliation behavior.
- Respect access controls, queues, rate limits, and explicit human verification. Fingerprint customization is not a substitute for permission or a guarantee of access.

## Migration requirements

1. Establish a Camoufox runtime adapter and install/browser provisioning instructions.
2. Validate Firefox persistent-profile behavior, process lifecycle, crash recovery, health, and encrypted profile checkpoint/restore in an isolated test environment.
3. Measure memory, startup time, monitored page stability, and p50/p95 operation latency; compare to existing runtime.
4. Exercise fixture-based retailer contract tests and controlled dry runs without final live purchase submission in CI.
5. Change the worker runtime selector only after all security and parity gates pass. Roll back via the prior runtime selector if regressions occur.

## Consequences

Camoufox is Firefox-based, not a drop-in Chromium or Patchright profile reader. Profile artifacts must be versioned by browser engine; do not restore a Chromium profile directly into Camoufox. Browser binaries and system packages must be provisioned separately. Existing platform infrastructure remains in scope; this is an execution-layer change, not a rewrite into a single-user local CLI.

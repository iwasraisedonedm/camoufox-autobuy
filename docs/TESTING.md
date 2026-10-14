# Testing Strategy

## Objective

Prove deterministic business behavior without requiring live retailer purchases in CI.

## Test layers

### Unit tests

Required for:

- Pydantic configuration models
- domain value objects
- purchase guards
- entitlement calculations
- state transitions
- error classification
- idempotency logic
- duplicate prevention
- repository rules
- worker lease logic
- pricing/allowance calculations

Unit tests must not require browser/network access.

### Persistence tests

Test against PostgreSQL-compatible behavior.

Cover:

- migrations
- uniqueness constraints
- transactional allowance decrement
- concurrency limits
- lease uniqueness
- ambiguous-attempt blocking
- order idempotency

### API tests

Cover:

- request validation
- authorization
- ownership checks
- error envelopes
- idempotency
- endpoint state transitions
- internal service permissions

### Discord adapter tests

Mock Discord transport and verify:

- command-to-API mapping
- account identity resolution
- stale interaction handling
- duplicate button idempotency
- status card rendering
- user-safe error rendering

Business rules should not live only in Discord tests.

### Worker protocol tests

Cover:

- registration
- heartbeat
- lease acquisition/renewal/release
- lease expiry
- safe reassignment
- worker loss
- single-writer profile lock
- profile checkpoint failure

### Retailer adapter tests

Use sanitized fixtures and mocked browser/page interfaces.

Cover:

- product identity normalization
- availability
- price parsing
- variant parsing
- cart result
- checkout preparation result
- confirmation parsing
- reconciliation behavior
- selector failure classification

Never store customer data or authenticated profile material in fixtures.

### Browser smoke tests

Local/staging only where appropriate:

- Patchright launches
- Chromium persistent context opens
- profile restore path works
- navigation works
- clean shutdown/checkpoint works

### Dry-run integration tests

Exercise as much of the real flow as possible while preventing irreversible purchase submission.

### Controlled live tests

Must be explicitly invoked outside CI.

Requirements:

- dedicated test account
- explicit operator authorization
- low-risk test item where practical
- strict max-price/quantity guards
- audit log
- post-test reconciliation

## CI policy

CI runs:

- dependency installation
- Ruff
- format check
- Pyright
- unit tests
- persistence/API tests with test services as appropriate
- coverage

CI must not:

- use real retailer accounts
- use real payment data
- restore production browser profiles
- submit live orders

## Coverage

Coverage percentage is not the only quality metric.

Require high coverage specifically around:

- guards
- state machines
- entitlements
- idempotency
- duplicate prevention
- ambiguous outcomes
- order confirmation
- lease recovery

## Regression fixtures

When retailer behavior changes, add a sanitized regression fixture reproducing the failure before fixing the adapter.

## Flake policy

Do not normalize flaky tests.

A flaky deterministic test is a defect. Browser/integration tests must use bounded timeouts and explicit waiting conditions.

## Release testing

Before production retailer release:

- full unit/API suite passes
- migrations validated
- worker recovery tested
- account-link flow tested
- retailer profile restore/checkpoint tested
- ambiguous outcome flow tested
- disconnect flow tested
- controlled adapter run meets reliability target

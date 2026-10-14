# Definition of Done

## Rule

A feature is not done because it works once.

It is done when it satisfies the applicable engineering, security, operational, and documentation requirements below.

## Functional

- requested behavior implemented
- expected success path tested
- relevant failure paths tested
- state transitions explicit
- no hidden retailer-specific behavior outside adapter boundary
- no undocumented side effects

## Types and contracts

- public interfaces typed
- domain models use canonical terminology from `CONTEXT.md`
- request/response models validated
- money uses Decimal
- enums/state values are centralized

## Persistence

If durable state changes:

- migration included
- migration reviewed
- rollback/compatibility considered
- indexes considered
- transaction boundary defined
- idempotency considered
- concurrency behavior considered

## Security

- no secrets or personal data committed
- no sensitive values logged
- authorization enforced
- resource ownership validated
- secrets retrieved through approved provider
- retailer profile handling follows `SECURITY.md`
- new attack surface documented

## Reliability

- retries bounded
- irreversible action retry behavior explicitly reviewed
- ambiguous outcome behavior defined
- worker/restart behavior considered
- dependency failure behavior considered
- timeout behavior defined

## Observability

- important state transitions logged
- correlation IDs present
- appropriate metric added
- operator-visible failure has reference ID
- alerting impact considered

## Testing

Applicable tests pass:

- unit
- persistence
- API
- worker protocol
- adapter fixtures
- integration

No live purchase is required or allowed in standard CI.

## Quality gates

Required commands:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

CI must pass.

## Documentation

Update the authoritative document when behavior changes:

- domain vocabulary → `CONTEXT.md`
- architecture/boundaries → `ARCHITECTURE.md`
- API → `API-CONTRACT.md`
- schema/domain entities → `DATA-MODEL.md`
- Discord UX → `DISCORD-SPEC.md`
- worker lifecycle → `WORKER-PROTOCOL.md`
- security → `SECURITY.md`
- states → `STATE-MACHINES.md`
- retailer adapter → `RETAILER-ADAPTER-SPEC.md`
- implementation order → `IMPLEMENTATION-PLAN.md`
- hard-to-reverse tradeoff → ADR

## Review

Before marking complete, the implementing agent must report:

- what changed
- tests run
- validation result
- migrations added
- architecture/docs changed
- unresolved risks or follow-ups

Do not report completion when required validation was not run or failed.

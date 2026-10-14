# AGENTS.md

## Mission

Build and maintain AutoBuy as a production-oriented hosted commercial purchasing platform.

The product is Discord-first, Best Buy-first, multi-customer, and server-operated. Customers do not receive the source code. Auto Purchase is the defining product capability; dry-run and assisted checkout are supporting modes.

The accepted architecture is a central control plane plus isolated retailer workers.

## Mandatory reading order

Before changing any subsystem, read:

1. `CONTEXT.md`
2. `ARCHITECTURE.md`
3. `docs/README.md`
4. the authoritative subsystem document(s)
5. relevant ADRs
6. `docs/V1-ACCEPTANCE.md`
7. `docs/DEFINITION-OF-DONE.md`

Do not silently override an accepted decision. If implementation reality conflicts with an authoritative document, surface the conflict and update the appropriate design document before introducing contradictory behavior.

## Authority map

- `CONTEXT.md` — canonical domain vocabulary
- `ARCHITECTURE.md` — system topology and boundaries
- `docs/IMPLEMENTATION-PLAN.md` — build order
- `docs/DATA-MODEL.md` — entities, schema, transactions
- `docs/API-CONTRACT.md` — control-plane interfaces
- `docs/DISCORD-SPEC.md` — Discord UX/commands
- `docs/WORKER-PROTOCOL.md` — leases, queues, recovery
- `docs/SECURITY.md` — security invariants
- `docs/STATE-MACHINES.md` — canonical runtime states
- `docs/ERROR-MODEL.md` — error taxonomy
- `docs/OBSERVABILITY.md` — logs, metrics, alerts
- `docs/DEPLOYMENT.md` — production deployment
- `docs/TESTING.md` — test and CI policy
- `docs/RETAILER-ADAPTER-SPEC.md` — retailer adapter contract
- `docs/PRICING-ENTITLEMENTS.md` — entitlement mechanics
- `docs/NON-GOALS.md` — explicit scope exclusions
- `docs/V1-ACCEPTANCE.md` — release bar
- `docs/DEFINITION-OF-DONE.md` — feature completion bar
- `docs/adr/` — accepted hard-to-reverse architecture decisions

## Core production stack

### Control plane

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2 async
- PostgreSQL
- Redis
- Discord client library
- structlog
- httpx
- Tenacity

### Worker plane

- Python 3.12+
- asyncio
- Patchright
- Chromium
- retailer adapter registry
- encrypted persistent retailer profiles
- retailer-specific queues
- renewable worker leases

### Development

- uv
- Alembic
- pytest
- pytest-asyncio
- pytest-cov
- Ruff
- Pyright
- GitHub Actions

## Hard architecture boundaries

1. PostgreSQL is durable truth.
2. Redis is ephemeral coordination only.
3. Discord is an interface, never authoritative state.
4. Unlock/payment service grants entitlements through authenticated API, never direct DB writes.
5. Retailer-specific behavior lives only in retailer adapters.
6. Patchright-specific implementation lives only in browser/worker infrastructure.
7. Retailer profile plaintext exists only in active worker runtime.
8. One active writer per RetailerProfile.
9. Workers are disposable compute.
10. Final purchase submission is never blindly retried.
11. Ambiguous purchase state blocks automatic resubmission until reconciliation.
12. CI never performs a live purchase.

## Repository direction

Use the architecture in `ARCHITECTURE.md`; do not preserve obsolete local-CLI assumptions.

Expected implementation shape:

```text
src/autobuy/
├── control_plane/
│   ├── api/
│   ├── services/
│   ├── repositories/
│   ├── auth/
│   └── settings/
├── discord/
├── domain/
├── persistence/
├── orchestration/
├── workers/
│   ├── browser/
│   ├── runtime/
│   └── profile_store/
├── adapters/
│   └── bestbuy/
├── observability/
└── common/
```

Do not create empty packages just to match this tree. Add code when behavior exists.

## Domain rules

Use terminology from `CONTEXT.md`.

Do not invent synonyms for core domain entities.

Important distinctions:

- CustomerAccount is not DiscordIdentity.
- ServiceEntitlement is not MonitoringJob.
- PurchaseTarget is reusable; MonitoringJob is one execution lifecycle.
- RetailerProfile is customer + retailer account/session identity.
- WorkerLease is ephemeral execution ownership.
- Successful Purchase Allowance counts confirmed units.
- Concurrent Job Limit is separate from purchase allowance.

## Data rules

- UUID primary keys.
- UTC timestamps.
- Decimal for money.
- explicit currency codes.
- Alembic migrations from the first production schema.
- transactional order confirmation + allowance decrement.
- optimistic versioning or DB locking where concurrent state mutation matters.
- no business truth stored only in Redis.

## Security rules

Never commit, log, fixture, or return:

- passwords
- cookies
- session tokens
- authorization headers
- encryption keys
- account-link tokens
- raw card data
- CVV/CVC
- browser profile contents
- production personal data

Production secrets belong in a secrets manager.

Retailer browser profiles use encrypted object storage and envelope encryption.

Do not collect retailer passwords through Discord.

If a retailer explicitly requires human verification/access control, transition to Action Required and hand control to the customer. Do not implement bypass logic for CAPTCHA, queues, purchase limits, authorization controls, or similar enforcement.

## Worker rules

- workers register and heartbeat
- leases are renewable and expire
- one active lease per retailer profile
- queue messages contain IDs/references, not secrets
- worker restores profile only after proving lease
- worker checkpoints encrypted profile before release
- plaintext profile copies are ephemeral
- safe states may be reassigned after worker loss
- ambiguous/irreversible states require reconciliation

## Retailer adapter rules

Every adapter conforms to `docs/RETAILER-ADAPTER-SPEC.md`.

Best Buy is the reference adapter.

Do not leak:

- selectors
- retailer-specific status text
- retailer page assumptions

outside the adapter boundary.

## State machine rules

Use `docs/STATE-MACHINES.md`.

Do not assign arbitrary state strings.

Persist important irreversible transitions before external side effects.

Before final submission, persist submission-start state.

Uncertain completion becomes AMBIGUOUS.

## API rules

Use `docs/API-CONTRACT.md`.

- versioned API
- strict Pydantic validation
- request IDs
- stable machine error codes
- internal service auth
- idempotency keys for sensitive mutations
- cursor pagination where collections can grow
- ownership authorization on every customer resource

## Discord rules

Use `docs/DISCORD-SPEC.md`.

Discord commands call the control-plane API.

Do not duplicate business logic in the Discord adapter.

Customer-visible errors are concise and include a support/reference ID.

## Observability rules

Use structured JSON logging in production.

Every purchase lifecycle should be traceable through stable IDs.

Do not dump raw HTML, headers, cookies, or browser storage into normal logs.

Add metrics for new operationally important behavior.

## Retry rules

Retries are only for safe/idempotent operations unless a specific documented state machine proves otherwise.

Never blindly retry:

- final order submission
- payment confirmation
- ambiguous mutations
- anything with unknown completion state

## Testing rules

Follow `docs/TESTING.md`.

Behavior changes require tests.

CI must never:

- restore production profiles
- use real retailer credentials
- use real payment data
- execute live purchase submission

Use sanitized fixtures for retailer adapter regression coverage.

## Dependency policy

Before adding a dependency, verify:

1. standard library is insufficient
2. dependency materially improves correctness/reliability/maintainability
3. project is maintained
4. Python 3.12+ supported
5. security/transitive cost is acceptable
6. it does not duplicate an existing dependency

Avoid premature infrastructure.

Do not add Kubernetes, event sourcing, public API frameworks beyond FastAPI, or additional data stores without a concrete documented requirement.

## Change control

Create/update an ADR only when a decision is:

- hard to reverse
- surprising without context
- the result of a real tradeoff

Do not create ADRs for routine implementation details.

## Validation before completion

Run all applicable checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

If migrations changed, validate migration upgrade/downgrade strategy as applicable.

If API behavior changed, update/tests contract.

If domain semantics changed, update `CONTEXT.md`.

If architecture changed, update `ARCHITECTURE.md` and relevant ADR.

## Completion reporting

Before calling work complete, report:

- files/behavior changed
- tests run
- validation results
- migrations added
- docs updated
- unresolved risks
- follow-up work

Never claim production readiness unless `docs/DEFINITION-OF-DONE.md` and relevant `docs/V1-ACCEPTANCE.md` criteria are actually satisfied.

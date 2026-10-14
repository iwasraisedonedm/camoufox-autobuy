# AGENTS.md

## 1. Project mission

Build and maintain a production-oriented automated purchasing framework using **Python 3.12+**, **Patchright**, and **Chromium**.

The system is designed around:

- persistent authenticated browser sessions
- low-latency product monitoring
- retailer-specific adapters behind stable interfaces
- deterministic purchase-state orchestration
- strict pre-purchase validation guards
- durable local persistence
- structured observability
- safe configuration and secret handling
- dry-run-first development
- CI that never performs live purchasing actions

The application should remain small, explicit, typed, testable, and easy to extend.

Do not turn this project into a generic scraping framework, a distributed crawler, or a collection of one-off retailer scripts.

---

## 2. Core stack

### Runtime

- Python 3.12+
- asyncio
- Patchright
- Chromium

### Configuration

- Pydantic v2
- pydantic-settings
- PyYAML

### CLI / operator interface

- Typer
- Rich

### Persistence

- SQLite
- SQLAlchemy 2
- aiosqlite

### Reliability / networking / logging

- Tenacity
- httpx
- structlog

### Development / quality

- uv
- pytest
- pytest-asyncio
- pytest-cov
- Ruff
- Pyright
- GitHub Actions

Do not introduce a new dependency unless it materially improves reliability, correctness, maintainability, or developer ergonomics.

Prefer the standard library when it is sufficient.

---

## 3. Architectural principles

The project must preserve the following separation of concerns.

```text
                           CLI
                            |
                            v
                    Settings Resolver
                            |
             +--------------+--------------+
             |              |              |
          Product         Profile        Secrets
          Config          Config          Store
             |              |              |
             +--------------+--------------+
                            |
                            v
                       Purchase Job
                            |
                            v
                     Purchase Engine
                            |
          +-----------------+------------------+
          |                 |                  |
        Guards           Monitor          Persistence
          |                 |                  |
          +-----------------+------------------+
                            |
                            v
                     Retailer Adapter
                            |
                            v
                     Browser Backend
                            |
                            v
                 Patchright + Chromium
                            |
                            v
                Persistent Warm Session
```

### Hard boundary rules

1. `settings/` owns configuration loading, validation, defaults, and resolution.
2. `browser/` owns Patchright/Chromium lifecycle and browser-specific implementation.
3. `adapters/` owns retailer-specific navigation, selectors, product parsing, cart logic, and checkout flow.
4. `monitor/` owns availability polling and monitoring orchestration.
5. `guards/` owns independent validation before a purchase can proceed.
6. `checkout/` owns purchase state transitions and workflow orchestration.
7. `persistence/` owns database access and durable records.
8. `events/` owns application event definitions and event publication/subscription if introduced.
9. `models/` owns domain models shared across layers.
10. Core application logic must never contain retailer-specific selectors.
11. Retailer adapters must not own global application configuration.
12. Core application code must not depend directly on Patchright outside `browser/`.
13. Persistence models must not leak SQLAlchemy-specific behavior into unrelated layers.
14. Configuration models must not become persistence models.
15. Browser profile data must never be tracked in Git.

If a change violates one of these boundaries, refactor the design instead of bypassing the boundary.

---

## 4. Intended repository architecture

Use the following structure unless there is a strong technical reason to change it:

```text
camoufox-autobuy/
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── config/
│   ├── app.yaml
│   ├── browser.yaml
│   ├── logging.yaml
│   ├── monitoring.yaml
│   ├── products.yaml
│   ├── profiles.example.yaml
│   ├── retailers.yaml
│   ├── workflow.yaml
│   └── README.md
│
├── data/
│   └── .gitkeep
│
├── logs/
│   └── .gitkeep
│
├── profiles/
│   └── .gitkeep
│
├── scripts/
│   ├── setup.sh
│   ├── smoke_test.py
│   └── doctor.py
│
├── secrets/
│   └── README.md
│
├── src/
│   └── autobuy/
│       ├── __init__.py
│       ├── cli.py
│       ├── exceptions.py
│       ├── logging.py
│       │
│       ├── settings/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   ├── models.py
│       │   ├── resolver.py
│       │   └── validation.py
│       │
│       ├── browser/
│       │   ├── __init__.py
│       │   ├── backend.py
│       │   ├── patchright_backend.py
│       │   ├── session.py
│       │   ├── profile.py
│       │   └── diagnostics.py
│       │
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── registry.py
│       │   └── <retailer>.py
│       │
│       ├── monitor/
│       │   ├── __init__.py
│       │   ├── watcher.py
│       │   ├── scheduler.py
│       │   └── availability.py
│       │
│       ├── checkout/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── state.py
│       │   ├── workflow.py
│       │   └── result.py
│       │
│       ├── guards/
│       │   ├── __init__.py
│       │   ├── purchase.py
│       │   ├── duplicate.py
│       │   └── authorization.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── product.py
│       │   ├── profile.py
│       │   ├── retailer.py
│       │   ├── job.py
│       │   ├── order.py
│       │   └── events.py
│       │
│       ├── persistence/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── models.py
│       │   ├── repository.py
│       │   └── migrations/
│       │
│       └── events/
│           ├── __init__.py
│           ├── bus.py
│           └── types.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── helpers/
│
├── .env.example
├── .gitignore
├── AGENTS.md
├── pyproject.toml
├── README.md
└── uv.lock
```

Do not create empty architectural layers merely to match this tree. Add a layer when its behavior is implemented.

---

## 5. Browser architecture

Patchright + Chromium is the primary browser implementation.

The application must depend on an abstract browser contract rather than importing Patchright everywhere.

### Required browser abstraction

```text
BrowserBackend
├── PatchrightBackend
├── CamoufoxBackend        # optional future backend
└── PlaywrightBackend      # optional diagnostic backend
```

The initial production path is:

```text
Python
  -> BrowserBackend
  -> PatchrightBackend
  -> Chromium
```

### Browser backend responsibilities

The browser layer may own:

- starting Patchright
- launching Chromium
- persistent browser contexts
- browser profile paths
- page creation/reuse
- timeouts
- locale/timezone configuration
- session restoration
- clean shutdown
- screenshots
- tracing
- diagnostic artifacts

The browser layer must not own:

- product prices
- cart business rules
- retailer-specific selectors
- purchase limits
- duplicate-order policy
- product identity validation

### Warm session model

The system should optimize for a long-running browser session:

```text
Persistent Chromium profile
        |
        +-- authenticated account state
        +-- retailer cookies/session
        +-- saved shipping where supported
        +-- saved payment method where supported
        |
        +-- monitor remains active
        |
        +-- checkout session remains ready
```

Avoid browser relaunches on the hot path unless recovery requires it.

---

## 6. Retailer adapter architecture

Every retailer must implement a stable adapter interface.

A retailer adapter may own:

- product URL navigation
- retailer-specific product identifiers
- variant detection
- price extraction
- availability extraction
- add-to-cart behavior
- checkout navigation
- retailer-specific account/session status
- retailer-specific order confirmation parsing

A retailer adapter must not own:

- global logging setup
- global application config
- persistence engine lifecycle
- cross-retailer duplicate logic
- product policy decisions
- generic retry rules
- secret storage strategy

### Adapter contract

The initial contract should conceptually cover:

```python
class RetailerAdapter(ABC):
    async def login_status(self) -> LoginStatus: ...
    async def product_snapshot(self, url: str) -> ProductSnapshot: ...
    async def add_to_cart(self, snapshot: ProductSnapshot, quantity: int) -> CartResult: ...
    async def prepare_checkout(self) -> CheckoutResult: ...
    async def submit_order(self) -> OrderResult: ...
```

Keep adapter methods narrow and deterministic.

Do not build giant retailer classes with unrelated responsibilities.

---

## 7. Product monitoring architecture

Monitoring and checkout must remain separate.

The monitor is responsible for:

- polling configured products
- obtaining current availability
- obtaining current price
- emitting availability changes
- respecting configured cadence
- backoff on transient errors
- health tracking
- stale detection

The monitor should produce a normalized event or snapshot rather than directly performing checkout.

Recommended flow:

```text
Monitor
  -> ProductSnapshot
  -> AvailabilityEvent
  -> PurchaseEngine
  -> Guards
  -> Checkout workflow
```

Do not bury checkout side effects inside monitoring code.

---

## 8. Purchase-state model

Checkout must use an explicit state machine.

Recommended states:

```text
IDLE
MONITORING
AVAILABLE
VALIDATING
ADDING_TO_CART
CART_CONFIRMED
CHECKOUT_READY
PURCHASE_AUTHORIZED
SUBMITTING
ORDER_CONFIRMED
REJECTED
FAILED
AMBIGUOUS
```

### State rules

- Every meaningful transition should be explicit.
- Illegal transitions should be rejected.
- Persist important irreversible transitions.
- Treat uncertain order submission as `AMBIGUOUS`, not success or failure.
- Do not silently reset from ambiguous state.
- Do not retry final submission automatically when completion is unknown.

---

## 9. Purchase guards

The purchase engine must independently verify the candidate before any irreversible action.

At minimum validate:

- retailer identity
- product identity
- expected variant
- quantity
- maximum unit price
- configured success limit
- duplicate-order state
- authorization mode
- current job enabled/active status

Guards should be:

- deterministic
- side-effect-light
- independently testable
- reusable across retailers

Retailer adapters may provide observed facts, but they should not decide whether those facts satisfy the configured purchase policy.

---

## 10. Idempotency and duplicate protection

Duplicate-order prevention is a production requirement.

Do not rely solely on:

- browser page state
- cart state
- button visibility
- in-memory flags

Use durable state where appropriate.

A successful purchase should produce a durable order/attempt record.

If final submission may have succeeded but confirmation is unavailable, mark the attempt `AMBIGUOUS` and require reconciliation before another submission attempt.

Do not automatically retry an irreversible operation with uncertain completion.

---

## 11. Retry policy

Use retries only where operations are safe and idempotent.

Appropriate retry targets:

- page navigation
- safe GET/read operations
- availability checks
- non-mutating DOM reads
- transient network failures
- recoverable browser actions before checkout submission

Do not blindly retry:

- final order submission
- payment confirmation
- irreversible mutations
- retailer actions with unknown completion state

Tenacity may be used for bounded retries.

All retry behavior should have:

- maximum attempts
- bounded wait
- logging
- clear failure state

---

## 12. Configuration architecture

Tracked configuration must remain non-sensitive.

### Tracked config

```text
config/
├── app.yaml
├── browser.yaml
├── logging.yaml
├── monitoring.yaml
├── products.yaml
├── profiles.example.yaml
├── retailers.yaml
└── workflow.yaml
```

### Local/private config

Real personal or secret data must live outside tracked config.

Preferred sources, in order:

1. OS-backed secret store / keyring
2. dedicated local ignored secret files
3. approved environment variables
4. retailer-saved account/payment/shipping state

### Configuration precedence

Use this precedence unless a documented exception is required:

1. explicit CLI flags
2. approved environment overrides
3. local ignored secret/profile config
4. tracked YAML config
5. application defaults

### Validation rules

- Validate configuration before browser startup.
- Use Pydantic models.
- Reject unknown fields where practical.
- Fail fast on invalid config.
- Do not silently coerce dangerous values.
- Use `Decimal` for monetary values in domain logic.

---

## 13. Secrets and personal data

Never commit or log:

- passwords
- card numbers
- CVVs/CVCs
- bank/account numbers
- routing numbers
- cookies
- session tokens
- OAuth tokens
- API keys
- recovery codes
- MFA backup codes
- browser profiles
- real addresses
- real phone numbers
- real email addresses
- production personal configuration

Prefer retailer-saved payment methods rather than storing raw payment-card data in this application.

Prefer persistent authenticated browser sessions rather than repeated credential entry.

Never add personal information to example files.

Example/config fixtures must use clearly synthetic values or logical references only.

---

## 14. Logging and observability

Use structured logging.

Meaningful events should include relevant non-sensitive metadata such as:

- job ID
- retailer
- product ID
- state
- attempt ID
- timestamp
- result
- retry count
- duration

Examples:

```text
JOB_STARTED
PRODUCT_CHECK_STARTED
PRODUCT_AVAILABLE
PRICE_ACCEPTED
GUARD_REJECTED
ADD_TO_CART_STARTED
CART_CONFIRMED
CHECKOUT_READY
SUBMISSION_STARTED
ORDER_CONFIRMED
SUBMISSION_AMBIGUOUS
JOB_DISABLED
```

Never log secrets.

Redact sensitive fields by key and by context.

Avoid dumping entire page HTML, request headers, cookies, or form bodies into normal logs.

---

## 15. Persistence

SQLite is the default production storage for the initial single-machine design.

Use SQLAlchemy 2 with async sessions.

Persistence should support, at minimum:

- jobs
- purchase attempts
- order outcomes
- important state transitions
- product observations if required
- reconciliation metadata for ambiguous submissions

Keep persistence APIs behind repositories/services.

Do not scatter raw SQLAlchemy session usage throughout the application.

Migrations should be introduced once schema evolution begins.

---

## 16. CLI design

The CLI is the primary operator interface for the first production version.

Preferred command shape:

```bash
autobuy config validate
autobuy products list
autobuy profiles list
autobuy browser smoke
autobuy browser login <retailer>
autobuy browser status <retailer>
autobuy monitor <product>
autobuy run <product> --dry-run
autobuy orders list
autobuy attempts list
autobuy doctor
```

CLI rules:

- destructive/irreversible actions must be explicit
- dry-run should be obvious
- errors should be concise but actionable
- output should not expose secrets
- Rich may be used for tables/status
- JSON output may be added later for automation

---

## 17. Testing strategy

Tests must favor deterministic behavior.

### Unit tests

Use unit tests for:

- configuration validation
- guards
- state transitions
- domain models
- repository logic
- retry policy
- duplicate detection

### Adapter tests

Use:

- mocked Patchright page objects
- stored sanitized HTML fixtures
- normalized retailer snapshots
- deterministic test data

### Integration tests

Integration tests may exercise:

- config loading
- database lifecycle
- browser backend startup
- dry-run workflows
- adapter orchestration with fixtures/mocks

### CI restrictions

CI must never:

- log into real retailer accounts
- use production credentials
- use real payment data
- place live orders
- depend on persistent authenticated profiles

Live browser tests should be explicitly invoked outside CI.

---

## 18. Code-quality rules

### Python

- Python 3.12+ syntax is allowed.
- Use type hints.
- Use `StrEnum`, dataclasses, and Pydantic where appropriate.
- Use `pathlib.Path` instead of raw path strings.
- Use `Decimal` for money.
- Prefer explicit return types.
- Prefer small pure functions for guards and validation.
- Keep async boundaries clear.
- Do not block the event loop with synchronous I/O.

### Error handling

- Raise domain-specific exceptions.
- Preserve exception chaining with `raise ... from exc`.
- Do not swallow exceptions silently.
- Differentiate transient, permanent, rejected, and ambiguous outcomes.
- Do not use broad `except Exception` unless performing cleanup or translating at a system boundary.

### Imports

- standard library
- third-party
- local imports

Use Ruff for ordering and formatting.

### Comments

Comment intent and invariants, not obvious syntax.

---

## 19. Performance rules

The primary latency bottlenecks are expected to be:

- retailer response time
- network latency
- browser rendering/navigation
- checkout flow complexity

Do not prematurely optimize Python micro-performance.

Prioritize:

- warm browser sessions
- minimal unnecessary navigation
- avoiding repeated login
- avoiding repeated profile creation
- async monitoring
- normalized retailer adapters
- efficient state handling
- minimal logging on the hot path

Measure before optimizing.

---

## 20. Browser stealth and compatibility

The browser layer should focus on compatibility, consistency, and predictable runtime behavior.

Do not add random stealth plugins or uncontrolled fingerprint mutation.

Prefer:

- persistent profiles
- coherent locale/timezone configuration
- stable browser environment
- consistent session behavior
- ordinary Chromium-compatible flows

Do not build features whose purpose is to bypass:

- CAPTCHAs
- virtual queues
- purchase limits
- account restrictions
- authorization controls
- access controls

If a retailer explicitly blocks automation, the adapter should surface that state rather than trying to defeat the restriction.

---

## 21. Git and repository practices

Use small, focused commits.

Preferred commit prefixes:

```text
feat:
fix:
refactor:
test:
docs:
chore:
ci:
perf:
```

Examples:

```text
feat: add persistent Patchright browser backend
fix: reject duplicate ambiguous purchase attempts
test: add price guard boundary coverage
docs: document local secret configuration
ci: add pyright and ruff checks
```

Do not commit generated browser artifacts, profiles, databases, secrets, or logs.

Keep `main` releasable.

For non-trivial features, prefer a branch and PR once the project reaches active implementation.

---

## 22. CI requirements

CI should run at minimum:

```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest --cov=autobuy --cov-report=term-missing
```

CI should use Python 3.12 initially.

Do not install or launch a production browser in CI unless a specific safe browser smoke job is later introduced.

Do not require secrets for standard CI.

---

## 23. Dependency policy

Before adding a dependency, ask:

1. Can the standard library solve this cleanly?
2. Does the package materially improve reliability or maintainability?
3. Is it actively maintained?
4. Does it support Python 3.12+?
5. Does it add transitive dependency or security risk?
6. Does it overlap an existing package?

Avoid framework sprawl.

Do not add:

- Redis
- Celery
- RabbitMQ
- PostgreSQL
- FastAPI
- Docker
- Kubernetes
- React
- Selenium

unless a concrete requirement justifies them.

---

## 24. Change-control rules for agents

Before modifying code:

1. Read this `AGENTS.md`.
2. Read `README.md`.
3. Read relevant files under `config/`.
4. Inspect existing architecture before introducing new abstractions.
5. Reuse established models/interfaces where possible.
6. Keep changes scoped to the requested task.
7. Do not rewrite unrelated files.
8. Do not silently weaken guards, validation, secret handling, or test coverage.
9. Preserve backward compatibility unless the task explicitly requires a breaking change.
10. Update documentation when architecture or operator behavior changes.

Before completing a task:

1. run lint
2. run format check
3. run type checks
4. run tests
5. report material architectural changes
6. report any unresolved failures
7. never claim success if validation did not pass

---

## 25. Production-readiness checklist

A feature is not production-ready unless applicable items are satisfied:

- typed interface
- validated config
- bounded retries
- explicit failure mode
- structured logs
- no secret leakage
- unit tests
- integration coverage where warranted
- idempotency considered
- duplicate behavior considered
- persistence considered
- cleanup behavior defined
- browser/session lifecycle defined
- dry-run behavior defined
- operator-visible error handling
- documentation updated

---

## 26. Initial implementation order

Use this order unless dependency relationships justify a change:

1. package/runtime baseline
2. configuration models and loaders
3. CLI shell
4. logging foundation
5. browser backend abstraction
6. Patchright persistent browser backend
7. browser smoke/doctor commands
8. core domain models
9. retailer adapter contract
10. purchase-state machine
11. purchase guards
12. persistence layer
13. monitor abstraction
14. first retailer adapter
15. dry-run workflow
16. fixture-driven adapter tests
17. controlled local integration tests
18. operator confirmation flow
19. live workflow only after review
20. additional retailer adapters

---

## 27. Validation commands

Agents must run these before considering implementation complete:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

When coverage is relevant:

```bash
uv run pytest --cov=autobuy --cov-report=term-missing
```

For browser setup on a local development machine:

```bash
uv run patchright install chromium
```

For application health:

```bash
uv run autobuy config validate
uv run autobuy browser smoke
```

---

## 28. Default decision rule

When multiple valid implementation approaches exist, prefer the one that is:

1. simpler
2. more explicit
3. easier to test
4. easier to reason about under failure
5. less coupled to a retailer
6. less coupled to Patchright internals
7. safer with secrets and state
8. easier to replace later
9. less dependency-heavy
10. operationally observable

Do not optimize for cleverness.

Optimize for reliability, determinism, maintainability, and fast recovery from failure.

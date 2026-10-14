# camoufox-autobuy

A Python-first automated purchasing framework built around **Camoufox**, **Playwright**, and a retailer-adapter architecture.

The project is designed to monitor configured products, validate purchase conditions, and execute controlled checkout workflows using authenticated browser sessions and explicit safety guards.

> **Repository status:** early-stage architecture and implementation.

## Goals

- Keep browser automation separate from retailer-specific logic.
- Support multiple retailers through a common adapter interface.
- Make products, profiles, limits, addresses, and account references easy to configure.
- Keep credentials, payment data, cookies, session state, and other secrets out of Git.
- Use deterministic Python for the purchase path.
- Use Camoufox CLI / agent tooling for setup, inspection, debugging, and adapter maintenance.
- Make purchase attempts observable, auditable, recoverable, and safe to test.
- Prevent duplicate orders, unintended quantities, and purchases above configured limits.

## Architecture

```text
                         CLI / Agent
                             |
                             v
                    Settings Resolver
                             |
          +------------------+------------------+
          |                  |                  |
       Product            Profile            Secrets
       Config             Config             Store
          |                  |                  |
          +------------------+------------------+
                             |
                             v
                       Purchase Job
                             |
                             v
                     Purchase Engine
                             |
           +-----------------+-----------------+
           |                                   |
           v                                   v
        Guards                           Retailer Adapter
           |                                   |
           |                                   v
           |                             Browser Manager
           |                                   |
           |                                   v
           +---------------------------> Camoufox
                                               |
                                               v
                                           Playwright
```

### Major layers

#### 1. Settings

Configuration is resolved into typed runtime models before a job starts.

Expected inputs:

- application settings
- product definitions
- retailer settings
- customer/profile settings
- shipping and billing references
- account references
- payment references
- environment variables / secret-store values

Secrets must never be committed to the repository.

#### 2. Browser

The browser layer owns Camoufox lifecycle and authenticated browser state.

Responsibilities include:

- start / stop
- persistent profiles
- browser contexts
- pages
- session restoration
- timeouts
- screenshots and debugging artifacts
- safe cleanup

The browser layer should not contain retailer-specific selectors or checkout rules.

#### 3. Retailer adapters

Each retailer implements a common interface.

Conceptually:

```python
class RetailerAdapter:
    async def login_status(self): ...
    async def get_product(self, url): ...
    async def check_availability(self, product): ...
    async def add_to_cart(self, product): ...
    async def prepare_checkout(self): ...
    async def submit_order(self): ...
```

Retailer-specific DOM selectors, navigation logic, and checkout details belong inside adapters.

#### 4. Monitor

Monitoring detects availability and emits an event or candidate purchase.

Monitoring and checkout remain separate so availability detection can evolve independently from order execution.

#### 5. Purchase engine

The purchase engine coordinates the workflow as an explicit state machine.

Example:

```text
IDLE
  |
  v
MONITORING
  |
  v
AVAILABLE
  |
  v
VALIDATING
  |
  v
ADDING_TO_CART
  |
  v
CART_CONFIRMED
  |
  v
CHECKOUT_READY
  |
  v
PURCHASE_AUTHORIZED
  |
  v
SUBMITTING
  |
  v
ORDER_CONFIRMED
```

Failure states should be explicit and persisted where useful.

#### 6. Guards

Checkout must pass independent validation guards before submission.

Initial guards:

- maximum price
- quantity
- duplicate-order prevention
- merchant / retailer validation
- product / variant validation
- authorization mode
- job success limit

Order submission must never be placed inside a generic retry loop.

#### 7. Persistence

SQLite is the initial persistence layer.

Expected records:

- jobs
- products
- runs
- availability events
- purchase attempts
- orders
- state transitions

The initial database should remain local and excluded from Git.

#### 8. Events and logging

Operational events should use structured logging.

Examples:

```text
JOB_STARTED
PRODUCT_AVAILABLE
PRICE_ACCEPTED
ADD_TO_CART_STARTED
CART_CONFIRMED
CHECKOUT_READY
ORDER_SUBMIT_STARTED
ORDER_CONFIRMED
JOB_DISABLED
```

Logs must redact passwords, card data, session tokens, cookies, authorization headers, and other sensitive values.

## Planned repository structure

```text
camoufox-autobuy/
├── .github/
│   └── workflows/
│       └── ci.yml
├── config/
│   ├── app.yaml
│   ├── products.yaml
│   ├── retailers.yaml
│   └── profiles.example.yaml
├── data/
├── logs/
├── profiles/
├── scripts/
├── secrets/
│   └── README.md
├── src/
│   └── autobuy/
│       ├── adapters/
│       │   ├── __init__.py
│       │   └── base.py
│       ├── browser/
│       │   ├── __init__.py
│       │   └── manager.py
│       ├── checkout/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   └── state.py
│       ├── events/
│       ├── guards/
│       ├── models/
│       ├── monitor/
│       ├── persistence/
│       ├── settings/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── models.py
│       ├── __init__.py
│       ├── cli.py
│       ├── exceptions.py
│       └── logging.py
├── tests/
│   ├── integration/
│   ├── unit/
│   └── fixtures/
├── .env.example
├── .gitignore
├── AGENTS.md
├── pyproject.toml
├── README.md
└── uv.lock
```

## Technology stack

### Runtime

- Python 3.12+
- asyncio
- Camoufox
- Playwright
- camoufox-cli

### Application

- Pydantic v2
- pydantic-settings
- PyYAML
- Typer
- Rich
- Tenacity
- structlog
- httpx

### Persistence

- SQLite
- SQLAlchemy 2
- aiosqlite

### Development

- uv
- pytest
- pytest-asyncio
- pytest-cov
- Ruff
- Pyright
- GitHub Actions

## Configuration model

Public/example configuration belongs in the repository.

Sensitive configuration does not.

Example:

```text
config/
├── app.yaml
├── products.yaml
├── retailers.yaml
└── profiles.example.yaml

secrets/
├── profiles.yaml
├── accounts.yaml
└── payments.yaml
```

A product definition should reference a named profile rather than duplicating personal information.

Example:

```yaml
products:
  example_product:
    retailer: target
    url: "https://example.com/product"
    quantity: 1
    max_price: 749.99
    profile: personal
```

A runtime profile may resolve:

```text
product config
    +
profile config
    +
environment / secret store
    +
persistent browser profile
    |
    v
validated PurchaseJob
```

## Secrets and payment data

Do not commit:

- passwords
- raw payment-card data
- CVVs
- session cookies
- browser profiles
- OAuth tokens
- API keys
- recovery codes
- authentication headers
- personal production configuration
- local databases containing sensitive data

Prefer retailer-saved payment methods and authenticated persistent browser sessions over storing raw card data in the application.

If local secret values are required, use environment variables or an OS-backed secret store/keyring.

## CLI direction

The application should expose a stable CLI instead of relying on standalone scripts.

Planned commands:

```bash
autobuy config validate
autobuy products list
autobuy profiles list
autobuy browser login target
autobuy browser status target
autobuy run example_product
autobuy run example_product --dry-run
autobuy orders list
```

`--dry-run` should exercise as much of the workflow as practical while preventing final order submission.

## Development principles

### Deterministic purchase path

The critical checkout path should use deterministic Python.

Agent/LLM tooling may assist with:

- browser inspection
- DOM analysis
- debugging
- selector maintenance
- generating test fixtures
- diagnosing retailer changes

It should not make uncontrolled purchase decisions at runtime.

### Async-first

Browser operations, monitoring, and persistence interfaces should be async-first to support concurrent jobs without unnecessary threads.

### Typed boundaries

Use Pydantic models and Python type hints at configuration, adapter, engine, persistence, and event boundaries.

Avoid passing unvalidated dictionaries throughout the application.

### Adapter isolation

Retailer-specific behavior belongs only in retailer adapters.

The purchase engine must not contain retailer-specific selectors or page assumptions.

### Safe retries

Retries are appropriate for transient, idempotent operations such as:

- page loads
- availability checks
- safe reads

Do not automatically retry:

- final order submission
- irreversible mutations
- operations whose completion state is uncertain

### Idempotency

A successful purchase should produce a durable record and, by default, disable or complete that job.

Duplicate-order protection should be enforced independently of UI state.

### Observability

Every meaningful state transition should be logged with structured fields such as:

- job ID
- retailer
- product ID
- state
- attempt ID
- timestamp
- result

Sensitive values must be redacted.

### Testability

Retailer adapters should support fixture-driven and mocked testing.

CI should not perform live purchases.

Use:

- unit tests
- mocked browser/page interfaces
- stored HTML fixtures where appropriate
- dry-run integration tests

Live retailer tests should remain controlled and explicitly invoked.

## Security baseline

- Keep the repository free of secrets.
- Maintain a strict `.gitignore`.
- Treat browser profiles as sensitive authentication material.
- Use unique account credentials and MFA where supported.
- Never log full payment details or authentication material.
- Keep dependencies pinned through `uv.lock`.
- Review dependency updates before merging.
- Run linting, type checks, and tests in CI.
- Use least-privilege GitHub tokens and repository permissions.
- Protect `main` once collaborative development begins.

## Automation scope

This project is intended for authorized purchase automation using the user's own accounts and ordinary retailer checkout workflows.

It is not intended to implement mechanisms for:

- CAPTCHA bypass
- queue bypass
- purchase-limit evasion
- account farming
- unauthorized access
- identity rotation intended to evade retailer controls
- proxy rotation intended to defeat enforcement

Retailer terms, rate limits, account restrictions, and applicable law remain external constraints of any deployment.

## Initial implementation sequence

1. Repository/tooling baseline
2. Configuration models and validation
3. CLI shell
4. Browser manager
5. Adapter interface
6. Purchase state model
7. Guard framework
8. SQLite persistence
9. Monitoring abstraction
10. First retailer adapter
11. Dry-run workflow
12. Controlled end-to-end testing
13. Additional retailer adapters

## Git workflow

Recommended branch model:

```text
main
  |
  +-- feat/*
  +-- fix/*
  +-- refactor/*
  +-- docs/*
```

Changes should be small, reviewable, and accompanied by tests when behavior changes.

Commit messages should describe the change directly, for example:

```text
feat: add typed purchase profile models
fix: prevent duplicate order submission after timeout
test: add price guard boundary coverage
docs: document persistent browser profile handling
```

## Current status

The repository is being initialized. The first implementation milestone is the application foundation: package configuration, settings, CLI, browser abstraction, adapter contract, state model, persistence, tests, and CI.

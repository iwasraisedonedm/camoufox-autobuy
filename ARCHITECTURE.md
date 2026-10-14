# Architecture

## Product

AutoBuy is a hosted commercial purchasing service. Customers interact through Discord, while retailer automation runs on provider-operated infrastructure. Best Buy is the first supported retailer.

The defining product capability is confirmed automatic purchasing. Dry-run and assisted checkout are supported operating modes, but they are not the commercial endpoint.

## System topology

```text
                           Customer
                              |
                           Discord
                              |
                              v
                     Discord Interface
                              |
                              v
                    Control Plane API
                         (FastAPI)
                              |
            +-----------------+------------------+
            |                 |                  |
        PostgreSQL          Redis          Object Storage
       durable truth      ephemeral       encrypted retailer
                          coordination      profile artifacts
            |                 |                  |
            +-----------------+------------------+
                              |
                              v
                     Worker Orchestrator
                              |
                        retailer queue
                              |
                              v
                      Worker Lease
                              |
                              v
                 Isolated Worker Container
                              |
                  Patchright + Chromium
                              |
                              v
                    Supported Retailer
```

## Control plane

The control plane owns authoritative business state and policy. It exposes the only supported write path for Discord, the unlock/payment service, and operator tooling.

Responsibilities:

- customer accounts
- linked Discord identities
- service entitlements
- supported retailer offerings
- purchase targets
- monitoring jobs
- job state
- retailer-profile metadata
- worker leases
- purchase attempts
- purchase outcomes
- allowance accounting
- entitlement expiration
- operator/admin actions

PostgreSQL is the system of record.

Discord is an interface adapter, never a source of truth.

## Worker plane

The worker plane executes retailer automation.

Workers are dynamically assigned through renewable leases. A worker restores the encrypted customer retailer profile, prepares the retailer runtime, monitors configured targets, and executes authorized purchase workflows through the retailer adapter.

Workers do not own customer or entitlement truth.

A worker may recover safe monitoring states after failure. It must not automatically repeat an irreversible action with uncertain completion.

## Customer retailer runtime

The effective isolation boundary is a customer retailer profile/runtime, not a globally shared browser context.

```text
Customer
  |
  +-- Best Buy Retailer Profile
  |      |
  |      +-- runtime lease
  |      +-- isolated Chromium profile
  |      +-- one live writer
  |      +-- one or more monitoring jobs
  |
  +-- Target Retailer Profile
         |
         +-- independent state
```

Only one active writer may modify a retailer profile at a time.

Multiple jobs for the same retailer profile should share one active retailer runtime rather than clone the browser profile into multiple writers.

## Retailer profile storage

Authenticated browser profiles are sensitive credential material.

Production flow:

```text
Encrypted profile artifact
        |
        v
Object storage
        |
        | authorized by active worker lease
        v
Ephemeral worker volume
        |
        v
Patchright / Chromium
        |
        v
Updated profile state
        |
        v
Encrypt and upload
        |
        v
Destroy plaintext worker copy
```

Use envelope encryption. A master key belongs in a KMS/secrets manager; customer retailer profiles use isolated data-encryption context.

The control plane stores encrypted-profile references and metadata, not routine plaintext profile material.

## Secrets

Local development may use ignored environment files.

Production secrets belong in a dedicated secret manager through a `SecretProvider` abstraction.

Examples:

- Discord token
- database credentials
- Redis credentials
- object-storage credentials
- internal service credentials
- encryption/KMS credentials

Raw customer credentials and payment-card data must not be collected through Discord.

## Customer identity

The canonical customer identity is the service-owned Customer Account.

Discord identities link to Customer Accounts.

```text
Customer Account
       |
       +-- linked Discord Identity
       +-- Service Entitlements
       +-- Retailer Profiles
       +-- Purchase Targets
       +-- Monitoring Jobs
```

Discord commands resolve the linked customer ID and then pass through backend authorization and entitlement checks.

## Account linking

Retailer credentials are not requested in Discord.

```text
/connect bestbuy
      |
      v
short-lived secure link
      |
      v
temporary hosted account-link session
      |
      v
customer authenticates with retailer
      |
      v
authenticated retailer profile persisted
      |
      v
Discord reports authentication success
```

If a retailer later requires reauthentication, jobs pause, the retailer profile enters `REAUTH_REQUIRED`, and the customer receives a secure resume link.

## Entitlements

Commercial entitlements are retailer-specific and may meter:

- duration
- concurrent monitored products/jobs
- confirmed successful units

Failed purchase attempts do not consume successful-purchase allowance.

An entitlement becomes unusable when either its time window expires or its purchase allowance is exhausted.

The payment/unlock bot is a separate system. It grants entitlements by calling a private authenticated API. It must not write directly to the AutoBuy database and Discord roles are not entitlement truth.

## Job model

A reusable Purchase Target describes the item.

A Monitoring Job represents one execution lifecycle.

A job snapshots important constraints at creation so active behavior does not silently change when defaults are edited.

Initial job data:

```text
job_id
customer_id
entitlement_id
retailer_profile_id
purchase_target_id
workflow_mode
max_price
quantity
success_limit
expires_at
status
created_at
```

V1 Purchase Target fields:

- retailer
- URL/navigation reference
- retailer product/SKU identity
- required variant when applicable
- maximum price
- quantity
- workflow mode
- success limit
- expiration

Substitute-product logic is not part of v1.

## Job states

Customer-visible states:

```text
AWAITING_COMMAND
AUTHENTICATION_REQUIRED
READY
MONITORING
ITEM_FOUND
VALIDATING
ADDING_TO_CART
CHECKOUT_PREPARING
AWAITING_CONFIRMATION
PURCHASING
PURCHASE_SUCCESSFUL
PURCHASE_FAILED
ACTION_REQUIRED
EXPIRED
PAUSED
ERROR
```

Internal state should be more detailed.

An uncertain final submission is `AMBIGUOUS`, never automatically retried.

## Purchase guards

Before final submission, validate:

- active entitlement
- supported retailer
- authenticated retailer profile
- target identity
- required variant
- quantity
- maximum price
- purchase allowance remaining
- concurrent-job rules
- profile/runtime lease validity
- duplicate-order state
- no unresolved ambiguous prior attempt
- job enabled/active status
- workflow authorization

Guard decisions should be deterministic and independently testable.

## Failure semantics

Internally distinguish at least:

```text
OUT_OF_STOCK
PRICE_REJECTED
VARIANT_UNAVAILABLE
ACCOUNT_REAUTH_REQUIRED
PAYMENT_DECLINED
RETAILER_REJECTED
CHECKOUT_ERROR
WORKER_ERROR
ENTITLEMENT_EXPIRED
PURCHASE_AMBIGUOUS
```

Customers receive concise friendly status plus a reference ID. Detailed diagnostics remain internal.

## Queue and orchestration

Redis is used for ephemeral coordination:

- retailer queues
- worker heartbeats
- renewable leases
- locks
- rate-limit counters
- status/event fan-out

Redis is not authoritative. Durable state remains in PostgreSQL.

Use retailer-specific queues so Best Buy capacity and incidents are isolated from future retailer adapters.

Workers are generic initially and load retailer adapters dynamically.

## Worker failure recovery

When a worker heartbeat stops:

1. lease expires
2. orchestrator evaluates the last durable job state
3. safe monitoring states may be reassigned
4. customer retailer profile is restored by a new worker
5. irreversible or ambiguous states require reconciliation before retry

## Monitoring

Customers do not choose polling frequency.

The service owns retailer-specific monitoring policy, including bounded backoff, jitter, rate limits, and health-state awareness.

Monitoring and checkout remain separate domains.

## Retailer health

Each supported retailer exposes an operational health state:

```text
HEALTHY
DEGRADED
OUTAGE
MAINTENANCE
```

Track:

- product-page success rate
- session validity rate
- cart success rate
- checkout preparation rate
- confirmed automation success rate
- median/p95 latency
- adapter exception rate

## Observability

Initial service metrics:

1. availability detection latency
2. item-found to cart latency
3. cart to checkout-ready latency
4. checkout-ready to confirmation latency
5. confirmed automation success rate
6. worker crash/recovery rate
7. retailer-session reauthentication rate
8. ambiguous-submission rate
9. queue wait time
10. active customers/jobs/workers

Target at least 95% successful execution of automation steps under normal supported-retailer conditions before an adapter is called production-ready. This does not guarantee retailer stock or retailer acceptance.

## Discord UX

Canonical flow:

```text
/shop
  -> choose retailer/package
  -> unlock/payment service grants entitlement

/connect bestbuy
  -> account-link session
  -> retailer profile authenticated

/autobuy
  -> URL
  -> variant
  -> quantity
  -> max price
  -> mode
  -> confirmation
  -> status card

Monitoring
  -> Item Found
  -> Purchasing
  -> Purchase Successful
  -> Awaiting Command
```

Support both structured slash commands and guided flows, with slash commands as the canonical command model.

Each monitoring job receives an editable status card. Important events also push dedicated messages. `/status` returns current state on demand.

V1 supports Discord server/private-channel usage and may also support DMs.

## Deployment

Initial production deployment is one Linux host with logically separated services.

```text
Linux Host
├── reverse proxy
├── control-plane API
├── Discord bot/gateway
├── worker orchestrator
├── PostgreSQL
├── Redis
├── object-storage client/service
└── worker containers
```

Use Docker Compose and/or systemd. Do not introduce Kubernetes for v1.

Restrict worker outbound network access where practical to required platform endpoints and supported retailer domains.

## Backups

Back up:

- PostgreSQL
- encrypted retailer-profile objects
- service configuration
- entitlement records
- purchase/order history

Redis must remain reconstructable.

## Data retention

Define exact retention durations before launch.

Policy direction:

- customer/account data: active lifetime plus defined retention period
- purchase/order metadata: longer support/accounting retention
- detailed browser diagnostics: short retention
- decrypted retailer profiles: never retained after worker teardown
- encrypted retailer profile: until disconnect/account deletion

`/disconnect <retailer>` pauses jobs, revokes runtime leases, invalidates the profile, and deletes the encrypted profile object.

## V1 product boundary

Auto Purchase is the core product.

V1 includes:

- customer account
- Discord linking
- private entitlement API
- Best Buy commercial offering
- Best Buy account linking
- encrypted persistent retailer profile
- product targets
- entitlement duration + concurrency + unit allowance
- warm retailer runtime
- product monitoring
- exact product and variant validation
- max-price and quantity guards
- automatic cart
- automatic checkout
- automatic final submission
- confirmed-order detection
- duplicate prevention
- ambiguous-outcome reconciliation
- Discord status cards
- push notifications
- status/stop/disconnect commands
- worker recovery
- operator admin commands
- structured logs/metrics
- PostgreSQL
- Redis
- encrypted profile storage
- tests and CI

Not v1:

- Telegram
- customer-facing multiple retailer accounts per retailer
- cross-retailer substitute products
- customer web/mobile dashboard
- public API
- Kubernetes
- multi-region deployment
- arbitrary unsupported websites
- AI deciding what to purchase
- customer-controlled polling frequency

## Technology direction

Control plane:

- Python 3.12+
- FastAPI
- Pydantic
- PostgreSQL
- SQLAlchemy
- Redis
- Discord library
- structured logging

Worker plane:

- Python 3.12+
- asyncio
- Patchright
- Chromium
- retailer adapter registry
- persistent retailer profiles
- bounded retry logic

Best Buy is the reference adapter. Additional retailers are chosen by commercial demand after Best Buy reaches production quality.


## Retailer execution transport

The platform above the retailer-adapter boundary is transport-agnostic. A supported retailer adapter may use browser automation, a retailer-supported structured interaction, or a combination of both for different operations.

Monitoring and checkout transport are independent implementation decisions. Selection is based on measured reliability and latency while preserving the same purchase guards, state transitions, idempotency rules, reconciliation behavior, and customer-visible outcomes.

The execution path should be prepared before an availability event whenever practical. Authenticated retailer state, normalized product identity, selected variant, purchase limits, and runtime readiness should already be established so Discord and avoidable setup work remain outside the latency-critical purchase path.

Discord remains the control and notification surface. It is not part of the hot execution path once a Monitoring Job is active.

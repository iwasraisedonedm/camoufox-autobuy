# Worker Protocol

## Purpose

Defines the contract between the control plane/orchestrator and isolated retailer workers.

## Principles

- transport abstraction is internal to the retailer adapter and worker runtime
- Discord and the control plane remain transport-independent


- Workers are disposable compute.
- PostgreSQL owns durable truth.
- Redis coordinates ephemeral work.
- One active writer per RetailerProfile.
- A worker may resume safe monitoring states.
- A worker must not automatically repeat an irreversible action with uncertain completion.

## Worker lifecycle

```text
STARTING
→ REGISTERED
→ IDLE
→ LEASED
→ RESTORING_PROFILE
→ RUNNING
→ CHECKPOINTING
→ IDLE
→ DRAINING
→ STOPPED
```

Failure may transition any active state to LOST.

## Registration

Worker registers:

- worker instance ID
- software version
- supported adapter versions
- capacity
- startup timestamp

The control plane returns worker identity and short-lived authorization.

## Queueing

Use retailer-specific queues.

Examples:

- `queue:bestbuy`
- `queue:target`

Queue entries contain only non-secret routing/job identifiers. Secrets and profile material are fetched through authenticated internal services.

## Lease acquisition

Lease binds:

- worker
- retailer profile
- one retailer runtime
- active job set
- expiration
- lease token

Invariant: one active lease per RetailerProfile.

Lease acquisition must be atomic.

## Heartbeats

Workers heartbeat on a fixed platform-controlled interval.

Heartbeat includes:

- worker ID
- lease ID
- runtime status
- current job IDs
- adapter health summary
- timestamp

Heartbeat does not contain secrets.

## Renewal

A valid worker renews before lease expiration.

Renewal fails if:

- worker revoked
- lease superseded
- retailer profile disconnected
- operator paused retailer/runtime
- lease token invalid

## Lease expiry

On missed heartbeats:

1. lease expires
2. runtime marked unavailable
3. orchestrator reads durable job/attempt state
4. safe states become eligible for reassignment
5. ambiguous/irreversible states become reconciliation-required
6. profile artifact ownership lock becomes available only after prior runtime is considered dead

## Job payload

Worker receives minimum necessary data:

- job ID
- customer ID
- entitlement ID/reference
- retailer profile ID/reference
- purchase target snapshot
- workflow mode
- guard policy snapshot
- lease expiry
- correlation ID

Do not embed credentials, cookies, card data, or decrypted browser profiles in queue messages.

## Profile restoration

Worker:

1. proves active lease
2. requests encrypted profile artifact
3. decrypts into ephemeral worker storage using approved key flow
4. starts Patchright/Chromium
5. verifies session
6. runs jobs

Only the leased worker may obtain decryption authorization.

## Profile checkpoint

Before normal release:

1. stop mutating browser state
2. flush browser/profile state
3. close or quiesce context
4. package profile
5. encrypt
6. upload new artifact version
7. atomically update artifact metadata
8. destroy local plaintext copy
9. release lease

## Events

Workers emit normalized events through internal API/event channel, including:

- worker started/stopped
- profile restored
- session verified/reauth required
- monitoring started
- product observation
- item available
- guard accepted/rejected
- cart result
- checkout prepared
- submission started
- order confirmed
- submission ambiguous
- job failed
- job completed

## Safe retries

Allowed for idempotent reads/navigation with bounded retry policy.

Never blindly retry:

- final submission
- payment confirmation
- any action whose completion state is unknown

## Recovery matrix

Safe to resume automatically:

- READY
- MONITORING
- ITEM_FOUND before irreversible mutation
- VALIDATING

Requires state-specific verification:

- ADDING_TO_CART
- CHECKOUT_PREPARING

Never auto-repeat without reconciliation:

- PURCHASING after submission signal
- AMBIGUOUS

## Shutdown

Workers support graceful drain:

- stop accepting new leases
- complete/checkpoint safe current work
- persist profile
- release lease
- exit

Forced termination relies on lease expiry and reconciliation rules.

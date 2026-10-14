# State Machines

## Rule

State transitions are explicit, validated, and persisted when operationally meaningful. Code must not assign arbitrary state strings.

## Monitoring Job state

Internal canonical states:

```text
CREATED
PREFLIGHT
READY
QUEUED
MONITORING
ITEM_FOUND
VALIDATING
ADDING_TO_CART
CART_CONFIRMED
CHECKOUT_PREPARING
CHECKOUT_READY
AWAITING_CONFIRMATION
PURCHASE_AUTHORIZED
SUBMITTING
ORDER_CONFIRMED
COMPLETED
PAUSED
ACTION_REQUIRED
FAILED
EXPIRED
STOPPED
AMBIGUOUS
```

### Happy path: auto purchase

```text
CREATED
→ PREFLIGHT
→ READY
→ QUEUED
→ MONITORING
→ ITEM_FOUND
→ VALIDATING
→ ADDING_TO_CART
→ CART_CONFIRMED
→ CHECKOUT_PREPARING
→ CHECKOUT_READY
→ PURCHASE_AUTHORIZED
→ SUBMITTING
→ ORDER_CONFIRMED
→ COMPLETED
```

### Assisted path

```text
CHECKOUT_READY
→ AWAITING_CONFIRMATION
→ PURCHASE_AUTHORIZED
→ SUBMITTING
```

### Failure rules

- pre-submit recoverable failure may return to MONITORING if policy allows
- explicit guard rejection returns to MONITORING or FAILED depending on reason
- human verification transitions to ACTION_REQUIRED
- entitlement expiry before checkout start transitions to EXPIRED
- user stop transitions to STOPPED unless an irreversible result is unresolved
- uncertain final submission transitions to AMBIGUOUS
- AMBIGUOUS may transition only through reconciliation to ORDER_CONFIRMED or FAILED

## Customer-facing mapping

```text
CREATED/PREFLIGHT      -> Ready / setup feedback
READY/QUEUED           -> Ready
MONITORING              -> Monitoring
ITEM_FOUND              -> Item Found
VALIDATING              -> Validating
ADDING_TO_CART          -> Adding to Cart
CART_CONFIRMED          -> Adding to Cart
CHECKOUT_PREPARING      -> Checkout Preparing
CHECKOUT_READY          -> Checkout Preparing
AWAITING_CONFIRMATION   -> Awaiting Confirmation
PURCHASE_AUTHORIZED     -> Purchasing
SUBMITTING              -> Purchasing
ORDER_CONFIRMED         -> Purchase Successful
COMPLETED               -> Awaiting Command
ACTION_REQUIRED         -> Action Required
FAILED                  -> Purchase Failed
EXPIRED                 -> Expired
PAUSED                  -> Paused
STOPPED                 -> Awaiting Command
AMBIGUOUS               -> Action Required / internal reconciliation
```

## RetailerProfile state

```text
DISCONNECTED
LINK_PENDING
AUTHENTICATED
READY
REAUTH_REQUIRED
LOCKED
DISCONNECTING
ERROR
```

Transitions:

- DISCONNECTED -> LINK_PENDING
- LINK_PENDING -> AUTHENTICATED | DISCONNECTED
- AUTHENTICATED -> READY
- READY -> REAUTH_REQUIRED | LOCKED | DISCONNECTING
- REAUTH_REQUIRED -> LINK_PENDING | DISCONNECTING
- LOCKED -> READY | ERROR
- DISCONNECTING -> DISCONNECTED

## ServiceEntitlement state

```text
PENDING
ACTIVE
EXHAUSTED
EXPIRED
REVOKED
```

Rules:

- ACTIVE -> EXHAUSTED when successful-unit allowance reaches zero
- ACTIVE -> EXPIRED when time window ends
- any non-final state may become REVOKED by authorized operator/service policy
- exhausted/expired/revoked entitlement cannot start new attempts

## PurchaseAttempt state

```text
CREATED
RUNNING
SUBMISSION_STARTED
CONFIRMED
REJECTED
FAILED
AMBIGUOUS
RECONCILING
```

Rules:

- SUBMISSION_STARTED must be persisted before irreversible submission
- uncertain completion -> AMBIGUOUS
- AMBIGUOUS -> RECONCILING
- RECONCILING -> CONFIRMED | FAILED
- no new submission may be created while a blocking ambiguous attempt exists

## Worker state

```text
STARTING
REGISTERED
IDLE
LEASED
RUNNING
DRAINING
STOPPED
LOST
```

## WorkerLease state

```text
ACTIVE
RELEASED
EXPIRED
REVOKED
```

At most one ACTIVE lease per RetailerProfile.

## Retailer health state

```text
HEALTHY
DEGRADED
OUTAGE
MAINTENANCE
```

Health transitions are based on measured platform signals, not individual customer errors alone.

# Error Model

## Principles

Errors are structured, stable, and machine-readable.

Every externally visible error contains:

- stable code
- concise user-facing message
- reference ID
- request/correlation ID where applicable

Internal logs retain diagnostic context without exposing secrets.

## Categories

### Customer/configuration

- `CUSTOMER_NOT_LINKED`
- `INVALID_TARGET`
- `INVALID_VARIANT`
- `INVALID_QUANTITY`
- `INVALID_MAX_PRICE`
- `JOB_NOT_FOUND`
- `JOB_NOT_ACTIVE`

### Entitlement

- `ENTITLEMENT_REQUIRED`
- `ENTITLEMENT_EXPIRED`
- `ENTITLEMENT_REVOKED`
- `ALLOWANCE_EXHAUSTED`
- `CONCURRENT_JOB_LIMIT_REACHED`

### Retailer profile/authentication

- `RETAILER_PROFILE_NOT_FOUND`
- `RETAILER_PROFILE_LOCKED`
- `RETAILER_REAUTH_REQUIRED`
- `ACCOUNT_LINK_EXPIRED`
- `ACCOUNT_LINK_INVALID`

### Product/monitoring

- `OUT_OF_STOCK`
- `PRICE_LIMIT_EXCEEDED`
- `VARIANT_UNAVAILABLE`
- `PRODUCT_IDENTITY_MISMATCH`
- `RETAILER_UNAVAILABLE`

### Checkout

- `ADD_TO_CART_FAILED`
- `CHECKOUT_PREPARATION_FAILED`
- `PAYMENT_DECLINED`
- `RETAILER_REJECTED`
- `PURCHASE_CONFIRMATION_FAILED`
- `PURCHASE_AMBIGUOUS`
- `DUPLICATE_PURCHASE_BLOCKED`

### Worker/platform

- `WORKER_UNAVAILABLE`
- `WORKER_LOST`
- `LEASE_INVALID`
- `LEASE_EXPIRED`
- `PROFILE_RESTORE_FAILED`
- `PROFILE_CHECKPOINT_FAILED`
- `DATABASE_UNAVAILABLE`
- `COORDINATION_UNAVAILABLE`
- `OBJECT_STORAGE_UNAVAILABLE`
- `INTERNAL_ERROR`

## Retry classification

Each error class has one retry policy:

- `NOT_RETRYABLE`
- `SAFE_RETRY`
- `RETRY_AFTER_BACKOFF`
- `ACTION_REQUIRED`
- `RECONCILIATION_REQUIRED`

Final order submission uncertainty always maps to `RECONCILIATION_REQUIRED`.

## HTTP mapping

Typical mappings:

- invalid request: 400
- unauthenticated: 401
- unauthorized/resource ownership: 403
- missing resource: 404
- state conflict/idempotency conflict: 409
- entitlement/rate policy: 422 or 429 as appropriate
- dependency unavailable: 503
- unexpected internal error: 500

Business failure such as out-of-stock is not necessarily an HTTP server error; endpoint semantics determine status.

## Discord rendering

Example:

```text
Purchase unsuccessful
Reason: The item exceeded your configured maximum price.
Reference: ATT-9K2F1
```

Do not expose internal exception names, selectors, stack traces, credentials, or raw retailer responses.

## Reference IDs

Generate opaque human-supportable IDs for important failures and purchase attempts. Reference IDs are searchable in logs and durable records.

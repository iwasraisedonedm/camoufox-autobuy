# API Contract

## Scope

The control-plane API is the only supported write boundary for Discord, the unlock/payment service, operator tooling, and workers.

Base path:

`/api/v1`

## Principles

- JSON request/response bodies.
- UTC ISO-8601 timestamps.
- UUID resource IDs.
- Idempotency for sensitive mutation endpoints.
- Request correlation ID on every request.
- Strict Pydantic validation.
- Stable machine error codes.
- No secrets returned in normal API responses.
- Internal and customer-facing authorization are separate concerns.

## Authentication

### Discord client

Discord gateway authenticates to the control plane as an internal service. Customer identity is derived from the linked Discord user ID.

### Unlock service

Uses internal service credentials with permission only to grant/query entitlements.

### Workers

Use short-lived worker identity plus lease-scoped authorization.

### Operator/admin

Uses a dedicated admin identity/role distinct from customer auth.

## Standard headers

- `X-Request-ID`
- `Idempotency-Key` for sensitive creates/mutations
- `Authorization`

## Error envelope

```json
{
  "error": {
    "code": "ENTITLEMENT_EXPIRED",
    "message": "The entitlement is no longer active.",
    "reference_id": "ERR-...",
    "request_id": "..."
  }
}
```

Never return stack traces to external clients.

## Endpoint families

### Health

- `GET /health/live`
- `GET /health/ready`

### Customers

- `POST /customers`
- `GET /customers/{customer_id}`
- `POST /customers/{customer_id}/discord-link`
- `DELETE /customers/{customer_id}/discord-link/{identity_id}`

### Entitlements

- `GET /customers/{customer_id}/entitlements`
- `POST /internal/entitlements/grant`
- `GET /internal/entitlements/{entitlement_id}`
- `POST /internal/entitlements/{entitlement_id}/revoke`

Grant requests must be idempotent using the unlock service's external grant reference.

### Retailer offerings

- `GET /retailers`
- `GET /retailers/{retailer_code}`
- `GET /retailers/{retailer_code}/health`

### Account linking

- `POST /customers/{customer_id}/retailer-profiles/{retailer_code}/link-session`
- `GET /account-link/{token}`
- `POST /account-link/{token}/complete`

Link tokens are short-lived, single-use, and stored hashed.

### Retailer profiles

- `GET /customers/{customer_id}/retailer-profiles`
- `GET /retailer-profiles/{profile_id}`
- `POST /retailer-profiles/{profile_id}/verify`
- `DELETE /retailer-profiles/{profile_id}`

Delete/disconnect pauses affected jobs and revokes active runtime leases.

### Purchase targets

- `POST /customers/{customer_id}/targets`
- `GET /customers/{customer_id}/targets`
- `GET /targets/{target_id}`
- `PATCH /targets/{target_id}`
- `DELETE /targets/{target_id}`

### Monitoring jobs

- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /customers/{customer_id}/jobs`
- `POST /jobs/{job_id}/start`
- `POST /jobs/{job_id}/pause`
- `POST /jobs/{job_id}/resume`
- `POST /jobs/{job_id}/stop`

Job creation performs entitlement and preflight validation.

### Attempts and orders

- `GET /jobs/{job_id}/attempts`
- `GET /attempts/{attempt_id}`
- `GET /customers/{customer_id}/orders`
- `GET /orders/{order_id}`

### Workers

Internal only:

- `POST /internal/workers/register`
- `POST /internal/workers/{worker_id}/heartbeat`
- `POST /internal/leases/acquire`
- `POST /internal/leases/{lease_id}/renew`
- `POST /internal/leases/{lease_id}/release`
- `POST /internal/jobs/{job_id}/events`
- `POST /internal/attempts/{attempt_id}/transition`
- `POST /internal/attempts/{attempt_id}/confirm-order`

## Idempotency

Require idempotency keys for:

- entitlement grants
- job creation
- order confirmation
- final state reconciliation

Server stores idempotency result metadata for a bounded retention window.

## Concurrency

Use optimistic versioning for mutable job records and database uniqueness/locking for entitlement and profile invariants.

## Pagination

Collection endpoints use cursor pagination. Do not expose offset pagination for large operational collections.

## Versioning

Breaking external/internal API changes require a new versioned contract or coordinated rollout. Do not silently change response semantics.

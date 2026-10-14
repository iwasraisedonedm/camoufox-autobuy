# Retailer Adapter Specification

## Purpose

Every supported retailer integration implements one normalized contract so the control plane and worker engine remain retailer-independent.

Best Buy is the reference adapter.

## Boundary

Retailer adapters own:

- retailer-specific URLs
- selectors
- product identifiers
- variant interpretation
- availability interpretation
- cart interaction
- checkout navigation
- order confirmation parsing
- retailer-session status
- retailer-specific reconciliation

Retailer adapters do not own:

- entitlement decisions
- customer authorization
- global retry policy
- persistence lifecycle
- worker leases
- encryption
- Discord behavior
- cross-retailer duplicate policy

## Required normalized models

### LoginStatus

Fields:

- authenticated
- reauth_required
- account_reference if safely available
- observed_at

### ProductSnapshot

Fields:

- retailer_code
- retailer_product_id
- retailer_variant_id
- title
- availability
- unit_price
- currency
- observed_at

### CartResult

Fields:

- accepted
- quantity
- cart_reference if available
- failure_code if rejected

### CheckoutResult

Fields:

- ready
- total if reliably observable
- currency
- action_required
- failure_code

### OrderResult

Fields:

- confirmed
- retailer_order_reference
- quantity_confirmed
- unit_price or confirmed total where available
- currency
- failure_code
- ambiguous

## Required adapter operations

Conceptual interface:

```python
class RetailerAdapter(Protocol):
    async def login_status(self) -> LoginStatus: ...
    async def product_snapshot(self, target: TargetSnapshot) -> ProductSnapshot: ...
    async def add_to_cart(self, product: ProductSnapshot, quantity: int) -> CartResult: ...
    async def prepare_checkout(self) -> CheckoutResult: ...
    async def submit_order(self) -> OrderResult: ...
    async def reconcile_order(self, attempt: AttemptSnapshot) -> OrderResult: ...
    async def health_check(self) -> RetailerHealthObservation: ...
```

Exact signatures may evolve, but responsibilities must remain equivalent.

## Product identity

Do not treat URL alone as canonical identity.

Validate:

- retailer code
- retailer product/SKU ID
- retailer variant ID where applicable

URL is a navigation reference.

## Availability

Normalize retailer-specific values into stable domain states such as:

- available
- unavailable
- unknown
- action_required

Do not invent availability when the page cannot be confidently interpreted.

## Money

Use Decimal and explicit currency.

Never use binary floating point for purchase decisions.

## Retry behavior

Adapter methods may classify errors, but the orchestration layer owns generic retry policy.

Safe read/navigation retries may be bounded.

Final submission must not be automatically repeated when completion is uncertain.

## Human-required steps

If the retailer requires reauthentication, OTP, CAPTCHA, or another explicit human verification/access-control step:

- report action required
- pause the workflow
- provide customer resume path

Do not make the adapter responsible for defeating access controls.

## Reconciliation

Every production adapter must implement an order reconciliation strategy sufficient to resolve ambiguous submissions where the retailer exposes usable order history/confirmation state.

If reconciliation cannot determine outcome, preserve AMBIGUOUS and escalate.

## Health

Adapter health observations feed retailer-level health state.

Health should distinguish:

- selector/DOM regression
- retailer outage
- authentication failure
- checkout rejection
- platform/worker failure

## Versioning

Retailer adapter version must be visible in worker registration and operational events.

Material selector/flow changes require regression tests.

## Production readiness

A retailer adapter requires:

- fixture-driven tests
- dry-run integration coverage
- account reauthentication path
- failure classifications
- order reconciliation path
- structured events
- production metrics
- documented known limitations
- controlled reliability testing meeting release target

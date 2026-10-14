# Domain Glossary

## Commercial Bot

A hosted purchasing service operated by the provider. Customers control it through a messaging interface and do not receive the source code.

## Customer Account

The canonical customer identity owned by the service.

A customer account is identified independently of Discord. Email/account identity is canonical; Discord is a linked interface identity.

## Messaging Interface

The customer-facing command and status surface.

Discord is the primary messaging interface for the initial product. Telegram may be supported later through the same domain commands and states.

The messaging interface is used to configure purchase targets, start or stop monitoring, inspect status, authorize supported workflows, and receive outcomes.

## Discord Identity

A Discord account linked to one Customer Account.

Discord is an interface identity, not the canonical customer record.

## Customer

A subscriber represented by one Customer Account and any linked interface identities.

A customer may hold multiple active service entitlements and retailer sessions.

## Service Entitlement

A commercial right to use a supported automation service under purchased limits.

Commercial packaging is based on retailer access plus purchased limits such as duration, concurrent monitored products/jobs, and successful purchase allowance. Failed purchase attempts do not consume successful-purchase allowance. Public package names and prices remain unresolved.

A service entitlement is distinct from a Purchase Target, Monitoring Job, and Retailer Session.

## Unlock Service

A separate payment/unlock system that grants or activates Service Entitlements for this bot.

The unlock service is a separate product/system and is not part of retailer checkout payment handling.

## Supported Retailer

A retailer explicitly selected by the operator and backed by a production-ready retailer integration.

The product supports a curated retailer list rather than arbitrary websites.

Best Buy is the first reference retailer.

## Retailer Session

A customer's authenticated session with a Supported Retailer.

The customer authenticates once through a temporary provider-controlled connection flow. After successful authentication, the customer-facing interface reports success and the service reuses the authenticated retailer session.

Retailer credentials should not be collected through Discord.

## Account-Link Session

A short-lived hosted session used to connect a customer's retailer account.

The customer completes retailer authentication in the temporary session. The resulting authenticated retailer state is then associated with the customer's isolated retailer profile.

## Customer Retailer Profile

The isolated customer-specific retailer identity and authenticated browser state used for that customer's jobs.

Customer retailer profiles must remain logically isolated from one another.

## Customer Runtime

The isolated execution context assigned to one customer while they have active work.

A Customer Runtime may include:

- the customer's retailer profile
- an isolated browser worker
- active monitoring jobs
- job state
- worker health

The preferred deployment model is an isolated worker/container per active customer, with persistent customer profile state mounted or restored as needed.

## Idle Runtime

A Customer Runtime with no active job.

The preferred lifecycle is to retain the runtime for a configurable idle period, then stop the browser/worker while preserving authenticated profile state.

## Purchase Target

A reusable retailer-specific item definition the customer wants monitored and potentially purchased.

For v1, a Purchase Target includes:

- retailer
- product URL/navigation reference
- product/SKU identity
- required variant where applicable
- maximum price
- quantity
- workflow mode
- success limit
- expiration

Substitute-product logic is out of scope for v1.

The domain should remain capable of later representing one logical desired item across multiple retailer listings.

## Monitoring Job

A single execution lifecycle for one configured Purchase Target and one customer.

A Monitoring Job belongs to a Customer and a Supported Retailer and remains active until it succeeds, expires, is stopped, reaches its configured success limit, or enters an unrecoverable state.

## Workflow Mode

The configured level of purchase automation for a Monitoring Job.

Supported modes are:

- Dry Run — monitor and validate without performing checkout mutations.
- Assisted Checkout — prepare the purchase flow and require customer confirmation before final submission.
- Auto Purchase — perform the authorized purchase automatically after configured guards pass.

## Success Limit

The maximum number of successful purchases permitted for a Monitoring Job.

The default is one successful order.

After the configured limit is reached, the job stops and the bot returns to Awaiting Command.

## Job Expiration

The point at which a Monitoring Job or relevant Service Entitlement is no longer allowed to begin a new purchase attempt.

If expiration occurs after a valid purchase workflow has already entered checkout, that in-progress workflow may finish once, but no new attempt begins afterward.

## Action Required

A customer-visible state used when a retailer requires human action such as re-authentication, OTP entry, payment confirmation, or another challenge.

The preferred behavior is to pause the workflow, notify the customer, and provide a secure resume/action link.

The system should minimize unnecessary challenges through stable authenticated sessions and consistent browser behavior, but should not depend on defeating retailer access controls.

## Ambiguous Outcome

A purchase attempt state where final submission may have succeeded but confirmation is unavailable.

The system must not automatically submit again. It should reconcile the customer's retailer account/order state before another purchase attempt is allowed.

## Bot State

A customer-visible operational state reported through the messaging interface.

Canonical customer-facing states are:

- Awaiting Command
- Authentication Required
- Ready
- Monitoring
- Item Found
- Validating
- Adding to Cart
- Checkout Preparing
- Awaiting Confirmation
- Purchasing
- Purchase Successful
- Purchase Failed
- Action Required
- Expired
- Paused
- Error

These customer-facing states may map to more detailed internal workflow states.

## Worker Lease

A temporary assignment of an isolated execution worker/container to an active customer job. Customer identity and retailer profile ownership remain persistent, while compute is dynamically assigned.

Workers recover safe monitoring states automatically after failure. Irreversible or ambiguous purchase stages require reconciliation before any replacement worker may retry.

## Successful Purchase Allowance

A purchased usage allowance measured by confirmed successful units rather than failed attempts. If one confirmed order contains multiple units, each confirmed unit consumes allowance. Concurrent monitoring capacity is metered separately from successful purchase allowance.

## Hosted Operator Service

The provider-operated service that runs the commercial bot and its retailer automation. The system is split into a central control plane and an isolated worker plane.

Customers interact with it remotely through the messaging interface and do not need direct access to the source code or automation host.

## Concurrent Job Limit

The maximum number of Purchase Targets a customer may actively monitor at the same time under a Service Entitlement.

Concurrent Job Limit is distinct from Successful Purchase Allowance.

## Partial Fulfillment

A purchase outcome where fewer units are confirmed than the job requested.

For v1, partial fulfillment is not intentionally accepted by default. If partial fulfillment occurs, only confirmed units consume Successful Purchase Allowance and the remaining requested quantity requires explicit job policy before continuing.

## Entitlement Exhaustion

The point at which a Service Entitlement is no longer valid because either its time window has expired or its Successful Purchase Allowance has reached zero.

No new purchase attempt may begin after entitlement exhaustion.

## Job Status Card

A persistent customer-facing status representation for a Monitoring Job in Discord.

A Job Status Card is updated as the job changes state. Important terminal events may also generate separate push notifications, while an on-demand status command returns current state.

## Retailer Offering

A customer-facing commercial product for one Supported Retailer, backed by the same shared platform and domain model.

Retailer offerings may be branded and sold separately even though they use the same underlying service architecture.

## Operator Control Plane

The provider-only interface for managing customers, entitlements, jobs, retailer/session health, workers, errors, and operational status.

The initial control plane should use CLI and/or Discord admin commands. A dedicated internal web admin panel may be added later. Discord is an interface only and is never the source of truth. Customer, entitlement, job, purchase, and retailer-session state belong to the service backend.

## Payment Method for Retailer Purchase

The mechanism used to fund a retailer purchase for a customer.

This remains separate from the Unlock Service and still requires a final product decision.

## Commercial MVP

The first sellable milestone must retain Auto Purchase as the defining product capability. Assisted checkout and dry-run remain supported modes, but the commercial product is not considered complete merely because it can monitor or prepare checkout. A confirmed successful automated purchase is the core success criterion.


## Retailer Transport

The internal execution mechanism used by a Supported Retailer adapter for a particular operation.

A Retailer Transport may be browser automation, a retailer-supported structured integration, or another explicitly supported mechanism. Monitoring transport and checkout transport may differ.

Transport selection is internal to the retailer adapter and does not change Customer, Monitoring Job, entitlement, or customer-facing Bot State semantics.

## Warm Retailer Runtime

A prepared Customer Retailer Profile runtime with authenticated retailer state and required execution prerequisites already available before a Monitoring Job needs to act.

A Warm Retailer Runtime exists to keep avoidable setup work outside active monitoring and checkout execution.

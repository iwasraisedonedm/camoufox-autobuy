# Domain Glossary

## Commercial Bot

A subscription-based purchasing service operated by the provider. Customers control it through a messaging interface and do not receive the source code.

## Messaging Interface

The customer-facing command and status surface.

Discord is the primary messaging interface for the initial product. Telegram may be supported later through the same domain commands and states.

The messaging interface is used to configure purchase targets, start or stop monitoring, inspect status, authorize supported workflows, and receive outcomes.

## Customer

A subscriber who uses the service through the messaging interface and may hold one or more active service entitlements.

## Service Entitlement

A commercial right to use a specific supported service for a defined period, scope, or usage allowance.

The exact packaging model is not yet fixed. Entitlements may vary by retailer, duration, concurrent jobs, successful purchases, or plan tier.

A service entitlement is distinct from a purchase target and a monitoring job.

## Supported Retailer

A retailer explicitly selected by the operator and backed by a production-ready retailer integration.

The product supports a curated retailer list rather than arbitrary websites.

Best Buy is the first reference retailer.

## Retailer Session

A customer's authenticated session with a supported retailer.

The customer authenticates once through a provider-controlled connection flow. After successful authentication, the customer-facing interface reports success and the service reuses the authenticated retailer session for later jobs.

The service should avoid requiring the customer to repeatedly provide retailer credentials.

## Customer Retailer Profile

The isolated customer-specific identity and authenticated retailer state used for that customer's jobs.

Customer retailer profiles must remain logically isolated from one another.

## Purchase Target

A retailer-specific item the customer wants monitored and potentially purchased.

A purchase target is identified by retailer, product identity, optional or required variant, navigation reference, configured quantity, and purchase constraints.

The model should support evolving from one retailer-specific listing to a logical desired item that may later map to multiple retailer listings.

## Monitoring Job

An active instruction to watch one configured purchase target for one customer.

A monitoring job belongs to a customer and a supported retailer and remains active until it succeeds, expires, is stopped, reaches its configured success limit, or enters an unrecoverable state.

## Workflow Mode

The configured level of purchase automation for a monitoring job.

Supported modes are:

- Dry Run — monitor and validate without performing checkout mutations.
- Assisted Checkout — prepare the purchase flow and require customer confirmation before final submission.
- Auto Purchase — perform the authorized purchase automatically after configured guards pass.

## Success Limit

The maximum number of successful purchases permitted for a monitoring job.

The default is one successful order.

After the limit is reached, the job stops and the bot returns to an awaiting-command state.

## Job Expiration

The point at which a monitoring job or service entitlement is no longer allowed to begin a new purchase attempt.

If expiration occurs after a valid purchase workflow has already entered checkout, that in-progress workflow may finish once, but no new attempt begins afterward.

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
- Expired
- Paused
- Error

These customer-facing states may map to more detailed internal workflow states.

## Hosted Operator Service

The provider-operated service that runs the commercial bot and its retailer automation.

Customers interact with it remotely through the messaging interface and do not need direct access to the source code or automation host.

## Payment Method for Retailer Purchase

The mechanism used to fund a retailer purchase for a customer.

This term remains unresolved for the current product. The user has indicated a separate crypto-wallet service may exist, but the relationship between that service and retailer checkout payment has not yet been defined.

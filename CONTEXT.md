# Domain Glossary

## Commercial Bot

A subscription-based product that customers operate through a messaging interface. The customer does not receive the source code.

## Messaging Interface

The customer-facing command and status surface delivered through Discord and/or Telegram.

The messaging interface is how customers configure a purchase target, start or stop monitoring, inspect status, and receive outcomes.

## Retailer Subscription

A time-bounded entitlement that grants a customer access to automation for one supported retailer.

Example: access to Target automation for one day.

A retailer subscription is distinct from a purchase target or monitoring job.

## Supported Retailer

A retailer for which the service has a production-ready adapter and an active commercial offering.

Best Buy is the first reference retailer.

## Purchase Target

A retailer-specific item the customer wants monitored and potentially purchased.

A purchase target is identified by retailer, product identity, optional/required variant, URL/navigation reference, configured quantity, and purchase constraints.

The model should support evolving from one retailer-specific listing to a logical desired item that can later map to multiple retailer listings.

## Monitoring Job

An active instruction to watch one configured purchase target for a customer.

A monitoring job is associated with a retailer subscription and remains active until it succeeds, expires, is stopped, or reaches its configured success limit.

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

## Bot State

A customer-visible operational state reported through the messaging interface.

Initial states include:

- Active
- Purchase Successful
- Purchase Unsuccessful
- Awaiting Next Command

These customer-facing states may map to more detailed internal workflow states.

## Customer

A subscriber who interacts with the service through Discord or Telegram and holds one or more retailer subscriptions.

## Operator Service

The server-side application and browser automation infrastructure that runs the commercial bot. Customers interact with it remotely and do not need direct access to the codebase or automation host.

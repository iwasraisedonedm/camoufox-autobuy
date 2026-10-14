# Discord Interface Specification

## Role

Discord is the primary v1 customer interface. It is not the source of truth.

Every Discord interaction resolves a linked Customer Account and delegates authorization and state changes to the control-plane API.

## Customer surfaces

V1 supports:

- private customer channels in the service Discord
- direct messages where operationally appropriate

Sensitive authentication is completed through secure short-lived web links, never through Discord messages.

## Commands

### /shop

Shows retailer offerings/packages available to the customer.

The unlock/payment service handles payment separately and grants the resulting entitlement through the private entitlement API.

### /connect <retailer>

Creates a short-lived retailer account-link session.

Response contains a secure single-use URL.

After successful retailer authentication, Discord reports:

`Retailer connected successfully.`

Do not ask for retailer passwords in Discord.

### /autobuy

Canonical job creation command.

Guided flow collects:

- retailer
- product URL
- product/SKU resolution
- required variant if applicable
- maximum unit price
- quantity
- workflow mode
- expiration when allowed by entitlement

The backend performs preflight validation before a job may enter READY.

### /status [job]

Returns current job state and relevant non-sensitive details.

### /stop <job>

Stops monitoring and prevents new purchase attempts.

If final submission is already in an uncertain irreversible state, stopping does not erase reconciliation requirements.

### /disconnect <retailer>

Pauses affected jobs, revokes active runtime ownership, deletes the encrypted retailer profile artifact, and marks the retailer profile disconnected.

### Admin commands

Admin commands are restricted to operator roles and call control-plane admin endpoints.

Initial admin actions:

- service status
- retailer health
- active jobs
- active workers
- failed/ambiguous attempts
- customer lookup
- entitlement lookup
- pause retailer
- resume retailer

## Status card

Each active job has one canonical editable status card.

Fields:

- retailer
- product
- variant
- quantity
- maximum price
- job state
- started time
- entitlement expiration
- allowance remaining where appropriate
- reference/job ID

Do not display secrets, full addresses, payment details, cookies, tokens, or internal stack traces.

## Customer-facing states

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

## Push notifications

Send dedicated notifications for:

- authentication required
- action required
- purchase successful
- purchase failed
- entitlement expired
- job stopped by operator
- retailer outage materially affecting the job

Routine polling does not generate chat spam.

## Interaction rules

- buttons/select menus must carry opaque internal IDs, not sensitive data
- interactions are authorized server-side
- stale component interactions must fail safely
- duplicate button presses must be idempotent
- customer-facing messages use concise reasons plus a reference ID
- technical diagnostics remain internal

## Job creation preflight

Before READY:

- customer linked
- entitlement active
- retailer enabled
- retailer profile authenticated
- product target valid
- variant resolvable
- quantity valid
- maximum price valid
- successful-unit allowance available
- concurrent-job capacity available
- no unresolved ambiguous attempt blocking the profile
- worker/runtime capacity available

## UX principle

Discord should feel like a control panel, not a raw terminal. Slash commands define the canonical operations; guided forms/buttons make those operations easier without creating a second business logic path.

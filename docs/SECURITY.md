# Security Model

## Security goals

Protect:

- customer identity
- retailer authenticated sessions
- service entitlements
- purchase integrity
- payment-related metadata
- service secrets
- operator access
- durable order history

## Trust boundaries

```text
Customer / Discord
      |
      v
Discord Adapter
      |
      v
Control Plane
      |
  +---+------------------+
  |                      |
PostgreSQL            Redis
  |
  +---- encrypted profile metadata
                         |
                         v
                  Object Storage
                         |
                  authorized lease
                         |
                         v
                  Worker Container
                         |
                         v
                     Retailer
```

## Secret classes

### Platform secrets

Examples:

- Discord bot token
- DB credentials
- Redis credentials
- object-storage credentials
- internal service credentials
- KMS credentials

Production storage: dedicated secrets manager.

### Customer retailer session material

Examples:

- cookies
- browser storage
- authenticated profile state

Storage: encrypted object artifact.

Treat this material as authentication credentials.

### Prohibited collection

Do not collect retailer passwords, raw payment-card data, CVV/CVC, MFA backup codes, or recovery secrets through Discord.

Prefer retailer-saved payment methods and customer-completed authentication flows.

## Encryption

Use envelope encryption for retailer profile artifacts.

Requirements:

- master key managed outside application data store
- per-profile data-encryption context
- authenticated encryption
- artifact versioning
- integrity validation before restore
- key rotation support

Never place master encryption keys in Git.

## Decryption policy

Only an actively leased worker may receive authorization necessary to decrypt a retailer profile.

The control plane should not routinely decrypt profiles.

Decrypted profile data exists only on ephemeral worker storage for the active runtime.

## Internal service authentication

All internal APIs require authenticated service identity.

Use short-lived credentials/tokens where practical.

Authorize by service role:

- Discord adapter
- unlock service
- worker
- operator/admin

The unlock service may grant entitlements but must not modify jobs/orders directly.

Workers may transition only resources covered by their active lease.

## Customer authorization

Every customer action resolves:

1. authenticated interface identity
2. Customer Account
3. resource ownership
4. active entitlement when required
5. operation-specific policy

Never trust resource IDs supplied by Discord without ownership validation.

## Account-link links

Requirements:

- random high-entropy token
- store token hash, not plaintext
- short expiration
- one-time use
- bind to customer + retailer
- HTTPS only
- invalidate on completion
- rate limit creation and use

## Database controls

- least-privilege DB users
- migrations under controlled role
- application cannot bypass row/domain validation services casually
- encrypted backups
- audit sensitive operator mutations

## Worker isolation

- isolated container/process per active retailer runtime
- one writer per RetailerProfile
- no shared writable browser profile
- minimal filesystem mounts
- non-root runtime
- read-only root filesystem where practical
- ephemeral profile workspace
- restricted outbound network access where practical
- no Docker socket access
- resource limits

## Logging

Never log:

- passwords
- cookies
- authorization headers
- session tokens
- encryption keys
- raw payment details
- full browser storage
- full account-link tokens

Use structured redaction before serialization.

Screenshots/traces are sensitive operational artifacts and use short retention.

## Rate limiting

Central policies cover:

- Discord commands
- account-link sessions
- job creation
- status queries
- internal API abuse
- retailer monitoring/actions

Customers do not control retailer polling frequency.

## Ambiguous purchase safety

If submission may have completed but confirmation is unavailable:

- mark attempt ambiguous
- block resubmission for that job/profile as required
- reconcile retailer order state
- require operator/customer action if automatic reconciliation is insufficient

This invariant overrides availability urgency.

## Backups

Back up:

- PostgreSQL
- encrypted retailer profiles
- configuration needed for restore
- purchase/order history

Do not treat Redis as authoritative backup data.

Restore procedures must preserve encryption/key compatibility.

## Incident response priorities

1. stop unauthorized purchase capability
2. revoke compromised service/worker credentials
3. pause affected retailer/profile/jobs
4. preserve audit evidence
5. rotate credentials/keys as required
6. restore verified state
7. communicate customer-impacting incidents appropriately

## Access-control boundary

The system may maintain consistent authenticated browser sessions and ordinary retailer workflows. When a retailer requires an explicit human verification or access-control step, pause and request customer action rather than attempting to defeat that control.

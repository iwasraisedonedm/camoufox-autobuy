# ADR 0003: Encrypted Customer Retailer Profiles in Object Storage

## Status

Accepted.

## Context

Authenticated Chromium profiles contain sensitive session material. A commercial service must move retailer sessions between dynamically assigned workers without exposing plaintext profiles broadly or relying on one worker host forever.

Sharing a profile between simultaneous writers is unsafe.

## Decision

Store customer retailer profiles as encrypted artifacts in object storage.

Use envelope encryption with key material managed through a production KMS/secrets system.

Only the actively leased worker for a retailer profile may retrieve and decrypt that profile.

The worker:

1. restores the encrypted profile into an ephemeral local volume
2. runs one active writer for that retailer profile
3. quiesces the browser before persistence
4. encrypts/uploads updated profile state
5. destroys the local plaintext copy after teardown

The control plane stores references and metadata rather than routinely handling plaintext browser profiles.

## Consequences

Positive:

- worker mobility
- profile isolation
- reduced control-plane exposure
- easier horizontal scaling and host replacement

Costs:

- encryption/key management
- profile upload/download lifecycle
- strict single-writer locking
- additional recovery handling for interrupted profile persistence

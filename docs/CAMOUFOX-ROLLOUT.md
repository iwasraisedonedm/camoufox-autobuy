# Camoufox browser runtime rollout

**Status:** architectural decision recorded; implementation is gated.

## Integration boundaries

Keep the existing control plane, Discord commands, PostgreSQL domain state, Redis leasing, encrypted object/profile store, and worker orchestration. Add a browser-runtime interface inside `src/autobuy/workers/`; only the retailer adapter and runtime implementation may depend on Camoufox specifics.

```text
Discord → Control-plane API → PostgreSQL/Redis → worker lease
  → customer-isolated worker → browser runtime (Camoufox)
  → retailer adapter → normalized events/reconciliation
```

## Compatibility checklist

- Confirm the installed Camoufox and Playwright versions are compatible with the supported Python 3.12 environment.
- Document how to provision the Camoufox browser binary in Docker/local environments.
- Validate launch, close, crash recovery, persistent state, and update policies.
- Never copy Chromium/Patchright profile directories into Firefox; persist browser-engine metadata with encrypted artifacts and require compatible restoration.
- Preserve one writer per retailer profile and redact cookies, tokens, and personally identifying browser diagnostics.
- Keep final order submission guarded; ambiguous outcomes require reconciliation before resubmission.
- Make the runtime selectable with a reversible configuration setting only once both engines pass tests.
- Measure actual p50/p95 latency and resources; do not claim 'instant' checkout or undetectable automation.

## Test gates

1. Unit tests for runtime lifecycle, engine-specific profile validation, cancellation, and failure cleanup.
2. Local smoke tests against a controlled storefront: login/session restore, availability observation, cart review, and shutdown.
3. Encrypted profile checkpoint/recovery under simulated worker loss.
4. Adapter contract parity and human-action-required handling.
5. CI lint, formatting, strict typing, test suite, and migration smoke tests.
6. Manual approval for promotion to the worker default.

**CI may not submit live retailer orders or use production credentials.**

## Follow-up implementation tasks

- Runtime abstraction and Camoufox lifecycle adapter.
- Browser binary provisioning and pinned dependencies/lockfile.
- Encrypted engine-specific profile storage and versioned artifact metadata.
- Worker health/metrics and context reuse.
- Sanitized browser smoke tests and staged worker runtime switch.

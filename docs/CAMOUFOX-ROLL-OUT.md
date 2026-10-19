# Camoufox browser-first rollout

The feature branch introduces a staged browser runtime. It **does not** enable
live purchase automation, retailer-specific selectors, account linking, or
encrypted profile restoration by itself.

## Local prerequisites

- Python 3.12+
- `uv sync --all-groups`
- `uv run camoufox fetch` (install the browser binary separately)
- Required Linux Firefox system libraries on the worker image

## Runtime contract

The worker obtains an exclusive, valid RetailerProfile lease first. The secure
profile-store restores the encrypted artifact to a temporary private absolute
path. It invokes `open_camoufox_profile(path)` inside the lease lifetime.
Only the owner may mutate the profile; on shutdown it closes the context,
checkpoints encrypted state and destroys the plaintext directory. Never put
plaintext profiles in Git, CI artifacts, routine logs, or durable volumes.

## Next integration gates

- Tests of lease ownership before restoration and teardown on lease loss
- Smoke test for Camoufox launch, navigation and clean shutdown in staging
- Encrypted profile restore/checkpoint and crash cleanup
- Session expiration and human-verification handoff
- Worker image with pinned/reproducible browser install
- Adapter fixture tests, outcome reconciliation and purchase guard tests
- Record p50/p95 browser startup and page observation latency

Until those gates pass, existing execution remains the default. No CI test
may use retailer credentials, checkout payment instruments or live orders.

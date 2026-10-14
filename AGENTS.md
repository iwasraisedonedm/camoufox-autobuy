# AGENTS.md

## Mission

Build a production-oriented Python application around Patchright + Chromium for product monitoring, persistent authenticated sessions, retailer adapters, deterministic validation, and safe assisted checkout workflows.

## Required boundaries

1. `settings/` validates external configuration.
2. `browser/` owns browser lifecycle and browser-specific behavior.
3. `adapters/` owns retailer-specific selectors and workflows.
4. `guards/` performs independent validation.
5. `persistence/` owns durable storage.
6. Core application logic must not contain retailer-specific selectors.
7. Core application code must not depend directly on Patchright outside `browser/`.

## Production rules

- Never commit or log passwords, card data, CVVs, cookies, tokens, recovery codes, or browser profiles.
- Prefer retailer-saved payment methods and persistent authenticated sessions.
- Dry-run is the development default.
- CI must never perform live purchases.
- Do not implement CAPTCHA bypass, virtual-queue bypass, purchase-limit evasion, or authorization-control bypass.
- Use explicit operator confirmation for irreversible actions until a retailer flow has been separately reviewed and approved.

## Engineering standards

- Python 3.12+.
- Async-first for I/O.
- Type public functions and important internal boundaries.
- Pydantic models for configuration and external data.
- Use pathlib.Path.
- Structured logging with secret redaction.
- Raise domain-specific exceptions rather than swallowing failures.
- Add tests with behavior changes.
- Avoid dependencies unless they materially improve reliability or reduce complexity.

## Validation

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

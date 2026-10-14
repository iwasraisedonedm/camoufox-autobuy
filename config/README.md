# Configuration

All tracked configuration in this directory must be non-sensitive.

## Files

- `app.yaml` — application-level paths and environment defaults.
- `browser.yaml` — Patchright/Chromium runtime behavior.
- `monitoring.yaml` — polling, concurrency, backoff, and health controls.
- `workflow.yaml` — dry-run behavior, validation guards, retries, and completion policy.
- `retailers.yaml` — retailer adapter registration and non-secret retailer settings.
- `products.yaml` — product jobs, limits, and profile references.
- `profiles.example.yaml` — example logical references only; never real personal data.
- `logging.yaml` — structured logging and redaction policy.

## Personal and secret data

Do not put names, addresses, phone numbers, email addresses, passwords, payment-card data, account numbers, cookies, tokens, or recovery material anywhere under tracked `config/`.

Real local profile data, if the application requires it, belongs in an ignored path such as:

```text
secrets/profiles.local.yaml
```

Prefer references to retailer-saved shipping/payment information and OS-backed credential storage where possible.

## Precedence

Recommended settings precedence, highest to lowest:

1. explicit CLI flags
2. approved environment overrides
3. local ignored secret/profile configuration
4. tracked YAML configuration
5. application defaults

Configuration should be validated before browser startup.

# Project Documentation

## Authority map

Each document has one primary responsibility. Avoid duplicating normative rules across files.

| Document | Authority |
|---|---|
| `../AGENTS.md` | How coding agents must work |
| `../CONTEXT.md` | Canonical domain vocabulary |
| `../ARCHITECTURE.md` | System topology and architectural boundaries |
| `IMPLEMENTATION-PLAN.md` | Build order and phase exit criteria |
| `DATA-MODEL.md` | Durable entities, relationships, transactions, and schema rules |
| `API-CONTRACT.md` | Control-plane API behavior |
| `DISCORD-SPEC.md` | Customer/operator Discord interaction contract |
| `WORKER-PROTOCOL.md` | Worker lifecycle, queues, leases, recovery, and profile handoff |
| `SECURITY.md` | Security invariants and trust boundaries |
| `STATE-MACHINES.md` | Canonical runtime states and transitions |
| `ERROR-MODEL.md` | Stable error taxonomy and retry classification |
| `OBSERVABILITY.md` | Logs, metrics, correlation, retailer health, and alerting |
| `DEPLOYMENT.md` | V1 production deployment and operations |
| `TESTING.md` | Test layers, CI policy, and controlled live testing |
| `RETAILER-ADAPTER-SPEC.md` | Contract for each supported retailer integration |
| `PRICING-ENTITLEMENTS.md` | Commercial entitlement mechanics |
| `NON-GOALS.md` | Explicit scope exclusions |
| `V1-ACCEPTANCE.md` | Product release acceptance bar |
| `DEFINITION-OF-DONE.md` | Feature-level completion standard |
| `adr/` | Accepted hard-to-reverse architecture decisions |

## Agent reading rule

Before changing a subsystem, read:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `ARCHITECTURE.md`
4. this index
5. the authoritative subsystem document(s)
6. relevant ADRs

Do not resolve conflicts by guessing. Surface the conflict and update the appropriate authoritative document before implementing contradictory behavior.

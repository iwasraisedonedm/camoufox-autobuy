# Deployment

## V1 deployment target

One production Linux host with logically isolated services.

Use Docker Compose and/or systemd. Do not introduce Kubernetes for v1.

## Service topology

```text
Internet
   |
Reverse Proxy / TLS
   |
   +-- Control Plane API
   +-- Account-Link Web Endpoint
   |
Internal Network
   |
   +-- Discord Gateway Service
   +-- Worker Orchestrator
   +-- PostgreSQL
   +-- Redis
   +-- Object Storage / Object Storage Client
   +-- Worker Containers
```

## Network zones

### Public

Only expose endpoints required for:

- HTTPS control-plane/account-link traffic
- Discord platform connectivity through outbound connections

Do not expose PostgreSQL, Redis, worker debug ports, or browser debugging endpoints publicly.

### Internal

Control plane, orchestrator, workers, DB, Redis, and object storage communicate on private networks.

### Worker egress

Restrict worker outbound access where practical to:

- supported retailer domains
- required DNS/time services
- approved object storage/KMS/internal endpoints

Do not grant workers access to Docker socket or host control APIs.

## Containers

Recommended services:

- `control-plane`
- `discord-bot`
- `orchestrator`
- `postgres`
- `redis`
- `object-storage` or external object-storage client
- `worker` replicas

Worker containers should:

- run as non-root
- use resource limits
- use ephemeral writable workspace
- mount no host secrets directly
- have no Docker socket
- receive short-lived service credentials
- be disposable

## Persistent storage

Persist:

- PostgreSQL data
- encrypted retailer profile objects
- required service configuration
- backup artifacts

Do not persist decrypted browser profiles after runtime teardown.

## Startup dependencies

Recommended order:

1. PostgreSQL
2. Redis
3. object storage
4. control plane
5. orchestrator
6. Discord bot
7. worker capacity

Services must still handle dependency outages gracefully rather than assuming perfect startup order.

## Health endpoints

Control plane:

- `/health/live`
- `/health/ready`

Readiness checks should verify required dependencies without performing destructive actions.

Workers report health through heartbeat and runtime status.

## Configuration environments

Maintain at minimum:

- local
- test
- staging
- production

Production secrets must not be copied into staging.

## Database migrations

Run Alembic migrations as an explicit deployment step.

Never auto-run destructive migrations inside arbitrary worker startup.

Migration process:

1. backup
2. review migration
3. apply
4. verify
5. deploy application version

## Backups

Back up:

- PostgreSQL
- encrypted retailer profiles
- configuration required for restore
- order/entitlement history

Redis is reconstructable and does not require authoritative backup.

Test restore procedures before launch.

## Rollback

A release must define:

- application rollback path
- migration compatibility strategy
- worker version compatibility window
- adapter rollback plan

Avoid schema changes that make immediate rollback impossible without an explicit migration strategy.

## Capacity

Initial capacity planning should measure:

- active Chromium runtimes
- RAM per retailer runtime
- CPU during checkout bursts
- worker startup time
- profile restore/checkpoint time
- queue wait time

Scale worker capacity before control-plane complexity.

## Production host hardening

At minimum:

- unattended or controlled security updates
- firewall
- SSH key authentication
- least-privilege service users
- encrypted disks where practical
- restricted admin access
- log rotation
- monitoring
- backup verification
- time synchronization

## Disaster recovery target

Before launch, document acceptable:

- RPO for PostgreSQL/profile objects
- RTO for control plane
- RTO for worker fleet
- customer notification procedure for extended outages

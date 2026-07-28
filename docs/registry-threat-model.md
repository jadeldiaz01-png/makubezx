# Registry threat model summary

## Status

`PROPOSED`

The authoritative decision and complete threat model are in ADR-0003. This summary exists to make the review gate explicit before implementation.

## Protected assets

- Tenant isolation.
- Agent identity and immutable version history.
- Canonical manifests and deterministic hashes.
- Capability indexes.
- Provenance and append-only audit records.

## Primary threats

- Cross-tenant data leakage or mutation.
- Tenant-context omission or spoofing.
- Duplicate, stale or conflicting writes.
- Manifest/hash tampering.
- Orphaned capability relationships.
- Unbounded queries and pagination abuse.
- SQL injection.
- Migration drift.
- Dependency and supply-chain compromise.

## Mandatory controls

- Explicit tenant context on every operation.
- Composite tenant-scoped constraints.
- Parameterized database access.
- Atomic manifest-plus-audit transactions.
- Immutable historical versions.
- Exact-match bounded searches.
- Stable keyset or cursor pagination.
- Canonical hash verification on write and read.
- Pinned dependencies and vulnerability auditing.
- Positive, negative and adversarial cross-tenant tests.

## Residual risks

No database, migration, credential or service exists on this branch. Production database operations, signatures, Policy Engine decisions, Runtime Admission and disaster recovery remain outside this architecture-review increment.

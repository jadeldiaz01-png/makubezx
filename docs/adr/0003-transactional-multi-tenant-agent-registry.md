# ADR-0003: Transactional multi-tenant agent registry with capability search

- Status: `PROPOSED`
- Date: 2026-07-27
- Owner: Platform Architecture / Backend & Distributed Systems / Data Architecture
- Risk: R2
- Issue: #12
- Base commit: `cc6a35dff9d8558853d794f1ba0ab46e549380d9`

## Context

The enterprise contracts merged in PR #11 provide deterministic validation boundaries for agent, tool, model, policy, evidence, certification, lease and approval data. They do not provide durable persistence, transactional history, tenant isolation or indexed discovery.

The inherited repository must not treat JSONL records, generated files, in-memory dictionaries or linear scans as an operational Registry. The platform requires a Control Plane inventory capable of managing more than 15,000 versioned agent definitions without implying that 15,000 agents are running.

## Problem

The next increment needs a Registry that can:

- persist immutable agent definition versions transactionally;
- isolate all reads and writes by tenant;
- search definitions by exact capability and governed metadata;
- provide stable pagination and bounded query sizes;
- detect conflicting writes and duplicate versions;
- retain provenance and an append-only audit trail;
- support reproducible benchmarks at 1,000, 5,000 and 15,000 definitions.

The Registry is inventory and history. It does not authorize execution.

## Decision proposed

Adopt a relational Registry architecture centered on PostgreSQL-compatible semantics, with schema migrations managed by Alembic and typed application boundaries that consume the existing enterprise contracts.

The implementation PR will introduce the minimum dependencies only after dependency, licence and vulnerability review. This ADR does not add a database, container, service, secret or runtime dependency by itself.

### Authority boundary

The Registry may:

- store canonical agent manifests and deterministic content hashes;
- store immutable versions and provenance metadata;
- expose tenant-scoped exact capability search;
- expose owner, risk, version and expiration filters;
- provide cursor-based or keyset pagination;
- record registry write audit events;
- reject conflicts, malformed contracts and cross-tenant access.

The Registry may not:

- decide policy or grant capabilities;
- approve or certify an agent;
- issue runtime leases;
- execute agents or tools;
- access model providers;
- expose unrestricted shell, filesystem or GitHub authority;
- use Redis for coordination in this increment;
- implement MCP, A2A, trading or social publishing.

## Data model principles

The detailed physical schema remains subject to implementation review, but the following invariants are mandatory:

1. Every row has an explicit tenant identifier.
2. Agent identity and semantic version form a tenant-scoped uniqueness boundary.
3. Stored manifest payloads use canonical JSON and retain their deterministic SHA-256 hash.
4. Historical versions are immutable; corrections create a new version.
5. Capability membership is normalized or otherwise indexed without unbounded linear scans.
6. Search ordering is deterministic and pagination is stable under concurrent inserts.
7. Writes use transactions and detect stale or conflicting updates.
8. Audit records are append-only from the application perspective.
9. Query limits are bounded and validated.
10. Expired or retired definitions remain historical records and are not silently deleted.

## Multi-tenancy

Application APIs and repository methods must require tenant context explicitly. Missing tenant context is a validation failure.

Cross-tenant reads, writes, uniqueness checks and capability searches must fail closed. Database constraints and query construction must reinforce, not replace, application-layer tenant validation.

Row-level security is classified as `ASSESS` for this increment. It may be adopted only if the PoC demonstrates that migration, testing and operational complexity are justified. Tenant predicates and composite constraints remain mandatory regardless.

## Search semantics

Initial capability search is exact-match and deny-by-default. Prefix, wildcard, fuzzy and semantic search are outside the first implementation because they can create ambiguous discovery and privilege-association risks.

Required filters:

- tenant;
- one or more exact capabilities;
- owner;
- risk level;
- semantic version;
- expiration state.

Required properties:

- deterministic ordering;
- bounded page size;
- stable pagination token or keyset;
- no cross-tenant result leakage;
- query plan evidence for benchmarked datasets.

## Transaction and concurrency model

The implementation must define explicit transaction boundaries. Registration of a manifest version and its audit record must succeed or fail atomically.

Duplicate `(tenant, agent_id, version)` registrations must fail. If mutable registry metadata is introduced, it must use optimistic concurrency with an explicit revision value; silent last-write-wins behavior is prohibited.

## Technology radar

- PostgreSQL relational persistence: `ADOPT` for the PoC and target architecture.
- Alembic schema migrations: `ADOPT`, subject to pinned dependency review.
- SQLAlchemy: `ASSESS` before implementation; compare typed SQLAlchemy 2.x with a narrower database adapter approach.
- Pydantic: `ASSESS`; existing immutable dataclass contracts remain the authority unless an adapter proves useful.
- Redis: `HOLD` for this PR.
- JSONL operational Registry: `REJECT`.
- Elasticsearch or vector search: `REJECT` for the initial exact capability use case.
- Kubernetes, Kafka and Temporal: `HOLD`.

## Alternatives considered

### JSONL with linear search

Rejected. It lacks transactional guarantees, stable concurrent writes, indexes, relational constraints and safe multi-tenancy.

### SQLite

Held for isolated tests only. It is not the target operational Registry because the required concurrency, deployment and PostgreSQL query-plan evidence would not be represented faithfully.

### Document database

Rejected for the first implementation. The main access patterns require strong uniqueness, transactions, relational capability membership, immutable version history and predictable indexes.

### In-memory Registry

Rejected as an operational solution. It may be used only as a test double and must not be represented as durable implementation.

## Threat model

### Assets

- tenant boundaries;
- agent identity and version history;
- canonical manifests and hashes;
- capability indexes;
- provenance and audit records;
- availability of Registry searches and writes.

### Threats

- cross-tenant leakage;
- tenant spoofing;
- duplicate or conflicting versions;
- manifest or hash tampering;
- orphaned capability references;
- unbounded query denial of service;
- pagination replay or result confusion;
- SQL injection;
- audit record mutation;
- stale writes and silent overwrite;
- migration drift;
- supply-chain compromise through new dependencies.

### Required controls

- explicit tenant context and composite constraints;
- parameterized database operations;
- canonical hash verification before persistence and after retrieval;
- bounded page sizes and timeouts;
- atomic manifest-plus-audit transactions;
- immutable history semantics;
- migration checks in CI;
- pinned direct dependencies and vulnerability audit;
- negative and adversarial cross-tenant tests;
- no database credentials in source, logs or test fixtures.

### Residual risks

- database operator access remains outside application tenant controls;
- production key management and signatures are not implemented;
- policy authorization is not part of the Registry;
- high availability, backups and disaster recovery are not claimed until restore and failover are tested in later infrastructure increments.

## Observability requirements

The implementation must emit structured, secret-free measurements for:

- registration outcome and stable error category;
- query outcome and result count bucket;
- transaction latency;
- capability-search latency;
- conflict and duplicate rates;
- cross-tenant denial count;
- migration version;
- connection-pool saturation if a pool is introduced.

Do not log raw manifests, prompts, credentials or personal data. Tenant identifiers must be pseudonymized or otherwise governed in telemetry.

## SLI proposals

These are acceptance targets, not current production measurements:

- cross-tenant records returned: 0;
- accepted hash mismatches: 0;
- silent duplicate versions: 0;
- unbounded search requests accepted: 0;
- deterministic pagination for an unchanged snapshot: 100%;
- successful manifest-plus-audit atomicity tests: 100%.

Latency and throughput SLOs will be set only after reproducible benchmarks.

## Benchmark plan

Generate deterministic synthetic manifests with fixed seeds and load:

- 1,000 definitions;
- 5,000 definitions;
- 15,000 definitions.

Measure at minimum:

- bulk registration duration;
- single registration latency distribution;
- exact capability search latency distribution;
- owner/risk/version filter latency;
- pagination latency;
- database size;
- relevant query plans and index usage.

The benchmark must record hardware or runner class, database version, migration revision, dataset seed, commands and commit SHA. No benchmark result may be claimed before execution.

## FinOps

ADR-only cost: $0 runtime infrastructure.

The implementation must document local/test database cost and provide a model for storage growth and query cost at 1,000, 5,000 and 15,000 definitions. Managed production database pricing remains outside this PR and must not be estimated as operational fact without a selected provider and measured workload.

## Migration strategy

The implementation will start with a single baseline migration and test both upgrade and downgrade in an ephemeral test database. Migration generation alone is insufficient; migration behavior must be executed in CI or an equivalent reproducible environment.

No existing production data migration exists in this increment.

## Rollback

Before merge: close the draft PR and delete the isolated branch if approved.

After merge but before downstream adoption: revert the merge commit and run the complete quality and supply-chain workflows.

If a database schema has been created in a test environment, execute the tested downgrade or destroy the ephemeral database. No production rollback is claimed.

## Acceptance gate for ADR approval

This ADR may move to `ADR_APPROVED` only after human review confirms:

- the Registry remains inventory rather than authority;
- PostgreSQL semantics are justified;
- Redis, Policy, Runtime and MCP remain out of scope;
- tenant isolation and immutable history are mandatory;
- benchmark evidence is required and cannot be invented;
- rollback and dependency-review requirements are acceptable.

Implementation must not begin before this gate is approved.

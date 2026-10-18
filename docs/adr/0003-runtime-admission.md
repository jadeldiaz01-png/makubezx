# ADR-0003: Deterministic runtime admission boundary

- Status: `IMPLEMENTING`
- Date: 2026-10-17
- Owner: Platform Architecture
- Supersedes: None

## Context

ADR-0002 defines immutable policy, agent, tool, evidence, certification, lease, and approval contracts, but it does not connect them at invocation time. A valid contract object alone must not grant runtime authority.

## Decision

Add `repo_agent_platform.core.runtime_admission.admit_tool` as a deterministic, no-side-effect evaluator. It admits one capability on one tool only when the agent is enabled at certified maturity; agent, tool, policy, evidence, certification, lease, tenant, and capability scopes match exactly; the evidence bundle contains the exact content hashes of the agent, tool, and policy manifests; evidence and certification bind to the expected immutable commit; the certification and lease are active; and any policy-required approval is current, exact, and independently decided.

Lease limits cannot exceed the agent's execution budget, and every granted lease capability must be within both the agent scope and policy allowlist. In this increment, only enabled `READ_ONLY` tools can be admitted. `WRITE_SCOPED` and `DESTRUCTIVE` remain unavailable under the current tool contract even when an approval exists.

Every outcome produces a redacted canonical decision event containing identifiers, capability, commit SHA, accepted approval reference when applicable, stable reason codes, timestamp, and a SHA-256 content hash. The caller supplies a canonical UUIDv4 invocation ID, making repeated evaluation of the same invocation reproducible. The caller must supply an audit sink with idempotent append semantics; reusing an event ID with different content must fail, and the sink must return `True` only after durable acceptance. The evaluator returns an allow only after that positive receipt; exceptions or any other return value yield denial.

## Consequences

- The evaluator is deterministic and adds no runtime dependency.
- It does not invoke tools, persist registries, or establish a trusted clock.
- Manifest hash binding is only as trustworthy as the supplied evidence and certification records; signature verification and trusted registry resolution remain required before production use.
- The audit hash detects content changes only when compared to a trusted retained event; it is not a signature, chain, or tamper-proof ledger.
- No production audit sink, signature/key management, transactional registry, replay store, or runtime integration is included. The platform remains `EXPERIMENTAL` and this ADR does not authorize deployment.

## Validation

Contract tests cover exact-SHA binding, tenant and scope mismatches, expiration/revocation, budget widening, approval binding, mutating-tool denial, canonical event hashing, and fail-closed audit errors. The pull-request workflow must pass against the exact proposed commit before this increment is marked `VALIDATED`.

## Rollback

Revert the commit introducing `runtime_admission.py`, its tests, and this ADR. No production state or credentials are changed.


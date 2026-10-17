# ADR-0003: Deterministic runtime admission boundary

- Status: `IMPLEMENTING`
- Date: 2026-10-17
- Owner: Platform Architecture
- Supersedes: None

## Context

ADR-0002 defines immutable policy, agent, tool, evidence, certification, lease, and approval contracts, but it does not connect them at invocation time. A valid contract object alone must not grant runtime authority.

## Decision

Add `repo_agent_platform.core.runtime_admission.admit_tool` as a deterministic, no-side-effect evaluator. It admits one capability on one tool only when the agent is enabled at certified maturity; agent, tool, policy, evidence, certification, lease, tenant, and capability scopes match exactly; evidence and certification bind to the expected immutable commit; the certification and lease are active; and any policy-required approval is current, exact, and independently decided.

Lease limits cannot exceed the agent's execution budget. In this increment, only enabled `READ_ONLY` tools can be admitted. `WRITE_SCOPED` and `DESTRUCTIVE` remain unavailable under the current tool contract even when an approval exists.

Every outcome produces a redacted canonical decision event containing identifiers, capability, commit SHA, stable reason codes, timestamp, and a SHA-256 content hash. The caller must supply an audit sink. The evaluator returns an allow only after the sink's `append` returns successfully; sink failure returns denial.

## Consequences

- The evaluator is deterministic and adds no runtime dependency.
- It does not invoke tools, persist registries, or establish a trusted clock.
- The audit hash detects content changes only when compared to a trusted retained event; it is not a signature, chain, or tamper-proof ledger.
- No production audit sink, signature/key management, transactional registry, replay store, or runtime integration is included. The platform remains `EXPERIMENTAL` and this ADR does not authorize deployment.

## Validation

Contract tests cover exact-SHA binding, tenant and scope mismatches, expiration/revocation, budget widening, approval binding, mutating-tool denial, canonical event hashing, and fail-closed audit errors. The pull-request workflow must pass against the exact proposed commit before this increment is marked `VALIDATED`.

## Rollback

Revert the commit introducing `runtime_admission.py`, its tests, and this ADR. No production state or credentials are changed.

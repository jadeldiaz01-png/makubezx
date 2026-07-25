# ADR-0002: Enterprise contracts as the platform authority boundary

- Status: `ADR_APPROVED`
- Date: 2026-07-25
- Owner: Platform Architecture
- Risk: R2
- Issue: #10

## Context

The inherited JSONL prototype describes generated agent records but is not an operational Registry, policy engine, runtime admission system, certification service, or durable evidence ledger. Downstream components require deterministic contracts before persistence or execution can be designed safely.

## Decision

Introduce immutable Python contracts for:

- `AgentManifest`
- `ToolManifest`
- `ModelManifest`
- `MCPServerManifest`
- `PolicyManifest`
- `QualityContract`
- `EvidenceBundle`
- `CertificationRecord`
- `RuntimeLease`
- `ApprovalRequest`

The contracts use only the Python 3.12 standard library in this increment. They provide fail-closed construction, strict identifiers and semantic versions, UTC timestamps, bounded budgets, explicit capabilities, deterministic canonical JSON and SHA-256 content hashes.

## Security invariants

- Deny by default cannot be disabled through a manifest.
- Wildcard and unrestricted capabilities are rejected.
- Non-read-only tools cannot be enabled by declaration alone.
- MCP remains read-only and disabled.
- Models cannot perform enabled silent fallback.
- An agent cannot be enabled before certification maturity.
- Runtime leases are scoped, expiring and revocable.
- Approval requester and approver must be different identities.
- Evidence is bound to an immutable Git commit SHA.
- Critical findings allowance remains zero.

## Separation of planes

These contracts belong to the Control Plane boundary. They do not implement Registry storage, Runtime execution, databases, Redis, AI Gateway, MCP transport, A2A, trading, social publication, secrets, or production deployment.

## Threat model

### Assets

Authority grants, tenant boundaries, evidence integrity, budgets, approvals and runtime admission inputs.

### Threats

Wildcard privilege expansion, confused deputy, self-approval, mutable evidence references, replay after expiration, silent model fallback, schema ambiguity, oversized execution and enabled-but-unimplemented declarations.

### Controls

Immutable values, exact-match capability decisions, canonical hashing, UTC TTL, separation of duties, bounded budgets and deny-by-default validation.

### Residual risks

- Python object validation is not persistence or distributed enforcement.
- Signatures and key management are not implemented.
- Cross-object referential integrity requires the future transactional Registry.
- Clock trust and replay protection require Runtime Admission infrastructure.

## Alternatives considered

### JSON Schema only

Rejected as the sole authority because application code would still need duplicated runtime semantics and cross-field validation.

### Pydantic dependency now

Held for later assessment. Adding a runtime dependency before the repository has a reviewed transitive lock would weaken the current supply-chain posture.

### Database schema first

Rejected because persistence design must depend on stable contracts, not define authority implicitly.

## Consequences

Positive: downstream Registry, Policy and Runtime increments receive a deterministic boundary with testable invariants.

Negative: contracts remain `EXPERIMENTAL` until independent review and integration with persistence, signatures, policy decisions and runtime admission.

## Rollback

Revert the PR introducing this ADR and `repo_agent_platform/contracts`. No migration, secret rotation or production state is involved.

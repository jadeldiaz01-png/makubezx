# Enterprise contracts

## Status

`EXPERIMENTAL`

These contracts are executable validation boundaries. They are not a Registry, policy decision point, runtime, certification authority, or deployment system.

## Local verification

```bash
python -m pip install -r requirements-dev.lock
python -m ruff check repo_agent_platform/contracts repo_agent_platform/tests/test_enterprise_contracts.py
python -m ruff format --check repo_agent_platform/contracts repo_agent_platform/tests/test_enterprise_contracts.py
python -m mypy repo_agent_platform/contracts repo_agent_platform/tests/test_enterprise_contracts.py
python -m pytest repo_agent_platform/tests/test_enterprise_contracts.py
python -m bandit -c pyproject.toml -r repo_agent_platform/contracts
```

The repository-level workflow additionally runs the complete test suite, coverage gate, immutable Action validation and dependency audit.

## Operational contract

Consumers must:

1. Construct contracts from trusted, authenticated inputs.
2. Reject `ContractError` without fallback or coercion.
3. Persist canonical JSON and its content hash together.
4. Bind approvals and evidence to immutable commit hashes.
5. Check certification and lease expiry using a trusted UTC clock.
6. Re-evaluate policy at runtime; a manifest never grants authority by itself.
7. Keep MCP, production deployment, live trading and automatic publishing disabled.

## Observability requirements for future consumers

Emit structured events without prompts, secrets or personal data:

- contract type and schema version;
- tenant pseudonymous identifier;
- validation outcome and stable error category;
- content hash prefix, never raw secret-bearing payloads;
- budget decision;
- certification/lease expiry outcome;
- policy decision and approval reference.

Cardinality must be bounded. Raw contract payloads are not logs.

## SLI proposal

- Contract validation determinism: 100% for identical canonical input.
- Invalid wildcard grants accepted: 0.
- Self-approval accepted: 0.
- Expired lease accepted: 0.
- Critical findings allowed: 0.

These are proposed integration SLIs, not measured production SLOs.

## FinOps

This increment adds no runtime provider, database, cache, cluster or model cost. Validation is local CPU and memory with linear complexity in tuple field sizes. Cost per 1,000 executions is not claimed until benchmarked in the Registry/Runtime integration environment.

## Runbook

### Validation failure

- Treat as deny.
- Record the contract type and error category.
- Do not mutate input to make it pass automatically.
- Return the item to its owner for correction.

### Hash mismatch

- Quarantine the artifact.
- Invalidate dependent certification and leases.
- Do not reconstruct evidence from mutable references.

### Suspected privilege expansion

- Revoke dependent leases.
- Activate the future runtime kill switch when available.
- Require a permission diff and independent approval.

## Rollback

Before merge: close the draft PR.

After merge: revert the merge commit, run `python-quality`, `governance-evidence` and `supply-chain-evidence`, and verify no downstream code imports the removed contracts. No database or production rollback exists in this increment.

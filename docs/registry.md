# Transactional agent Registry — architecture review

## Status

`PROPOSED`

This document supports review of ADR-0003. No Registry service, database, migration, runtime dependency or operational persistence has been implemented yet.

## Scope of the current branch

- Issue #12.
- ADR-0003.
- Architecture, threat-model, benchmark and rollback requirements.

## Explicitly not implemented

- PostgreSQL service or connection configuration.
- SQLAlchemy, Alembic or Pydantic dependencies.
- Database models or migrations.
- Registry API or repository implementation.
- Redis, Policy Engine, Runtime Admission, MCP or A2A.
- Production deployment, secrets or credentials.

## Architecture review checklist

- [ ] Registry is inventory and history, not execution authority.
- [ ] Every read and write requires explicit tenant context.
- [ ] Agent versions are immutable.
- [ ] Capability search is exact-match and bounded.
- [ ] Search ordering and pagination are deterministic.
- [ ] Manifest and audit writes are atomic.
- [ ] Cross-tenant access fails closed.
- [ ] JSONL is not an operational Registry.
- [ ] Redis, Policy, Runtime and MCP remain outside this PR.
- [ ] Benchmark results cannot be claimed before execution.
- [ ] New dependencies require pinned versions, licence review and vulnerability audit.

## Validation for this documentation-only commit

```bash
python repo_agent_platform/tools/validate_workflows.py
```

The normal repository workflows remain the source of truth. No benchmark or database test is applicable until the ADR receives independent approval and implementation begins.

## Rollback

Close the draft PR and delete `registry/transactional-agent-registry`, or revert its documentation commit. No database, migration, secret or production state exists.

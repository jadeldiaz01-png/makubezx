# Runtime Admission Implementation Plan

> **For agentic workers:** Required sub-skill: `superpowers:executing-plans`. Steps use checkbox syntax for tracking.

**Goal:** Add deterministic, fail-closed admission for a single tool invocation using the existing enterprise contracts.

**Architecture:** A pure control-plane evaluator checks exact identity, tenant, capability, commit, certification, lease, budget, and approval relationships. It emits a redacted SHA-256-bound decision event and returns allow only after a caller-supplied audit sink accepts that event. No tool is executed by this module.

**Tech Stack:** Python 3.12 standard library; existing immutable `repo_agent_platform.contracts`.

**Spec:** `docs/adr/0003-runtime-admission.md`

## Global Constraints

- Deny by default; match all identifiers and capabilities exactly.
- Bind evidence to the caller-supplied immutable 40-character commit SHA.
- Only enabled, read-only tools may be admitted in this increment.
- Audit persistence must complete before an allow decision is returned.
- Do not add runtime dependencies or modify production state.

## Review Focus

- Wrong commit, certification hash, or tenant must deny admission.
- Expired, revoked, or not-yet-valid evidence must deny admission.
- Lease scopes or budgets wider than the agent must deny admission.
- A lease containing any capability outside the agent or policy scope must deny the whole lease.
- Write and destructive tools must remain denied despite approval.
- Repeated evaluation with the same UUIDv4 invocation ID must emit identical audit data.
- An admitted approval-gated decision must retain its exact approval request ID.
- Audit sink failure must never return an allow decision.

---

### Task 1: Contract tests

**Files:**
- Create: `repo_agent_platform/tests/test_runtime_admission.py`

- [x] Add tests for one valid read-only admission, SHA/certification/tenant mismatches, expiry/revocation, budget widening, approval binding, mutating-tool denial, and audit failure.
- [x] Run the test module and confirm it fails because the admission module does not exist.

### Task 2: Deterministic admission and audit event

**Files:**
- Create: `repo_agent_platform/core/runtime_admission.py`
- Create: `docs/adr/0003-runtime-admission.md`

- [x] Implement exact-match cross-contract validation and stable denial codes.
- [x] Create redacted canonical audit events with SHA-256 content hashes.
- [x] Require an audit sink before returning allow; fail closed when appending raises.
- [x] Deny the entire lease if any granted capability exceeds agent or policy authority.
- [x] Use a caller-supplied UUIDv4 invocation ID for repeatable audit event identity.
- [x] Record the accepted approval request ID in the audit event.
- [x] Keep write/destructive tools unavailable under the existing manifest contract.
- [x] Run all package tests, workflow/catalog validators, sample generation/validation, Ruff, compileall, and mypy.

### Task 3: External exact-SHA review

**Files:**
- GitHub branch and draft pull request based on the observed source commit.

- [ ] Confirm pull-request workflow results at the exact proposed commit.
- [ ] Keep runtime integration, durable audit service, signatures, key management, and production certification as subsequent gates.

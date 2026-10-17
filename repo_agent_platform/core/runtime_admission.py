from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from repo_agent_platform.contracts import (
    AgentManifest,
    ApprovalRequest,
    CertificationRecord,
    Decision,
    EvidenceBundle,
    Maturity,
    PolicyManifest,
    RuntimeLease,
    ToolEffect,
    ToolManifest,
)

_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class AuditSink(Protocol):
    """A sink must durably append before returning; production adapters own that guarantee."""

    def append(self, event: AuditEvent) -> None: ...


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    occurred_at: datetime
    tenant: str
    agent_id: str
    tool_id: str
    capability: str
    commit_sha: str
    allowed: bool
    reason_codes: tuple[str, ...]
    event_hash: str

    def canonical_json(self) -> str:
        return json.dumps(
            {
                "agent_id": self.agent_id,
                "allowed": self.allowed,
                "capability": self.capability,
                "commit_sha": self.commit_sha,
                "event_id": self.event_id,
                "occurred_at": self.occurred_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                "reason_codes": self.reason_codes,
                "tenant": self.tenant,
                "tool_id": self.tool_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    allowed: bool
    reason_codes: tuple[str, ...]
    audit_event: AuditEvent
    audit_persisted: bool


def _event(
    *,
    now: datetime,
    agent: AgentManifest,
    tool: ToolManifest,
    capability: str,
    commit_sha: str,
    allowed: bool,
    reasons: tuple[str, ...],
) -> AuditEvent:
    event_id = str(uuid.uuid4())
    payload = {
        "agent_id": agent.agent_id,
        "allowed": allowed,
        "capability": capability,
        "commit_sha": commit_sha,
        "event_id": event_id,
        "occurred_at": now.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "reason_codes": reasons,
        "tenant": agent.tenant,
        "tool_id": tool.tool_id,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return AuditEvent(
        event_id,
        now,
        agent.tenant,
        agent.agent_id,
        tool.tool_id,
        capability,
        commit_sha,
        allowed,
        reasons,
        digest,
    )


def admit_tool(
    *,
    agent: AgentManifest,
    tool: ToolManifest,
    policy: PolicyManifest,
    evidence: EvidenceBundle,
    certification: CertificationRecord,
    lease: RuntimeLease,
    capability: str,
    expected_commit_sha: str,
    now: datetime,
    audit_sink: AuditSink,
    approval: ApprovalRequest | None = None,
) -> AdmissionDecision:
    """Evaluate one tool invocation; return allow only after the audit sink accepts it."""
    reasons: set[str] = set()
    if now.tzinfo is None or now.utcoffset() != UTC.utcoffset(now):
        raise ValueError("now must be timezone-aware UTC")
    if not _SHA_PATTERN.fullmatch(expected_commit_sha):
        reasons.add("expected_sha_invalid")
    if evidence.commit_sha != expected_commit_sha:
        reasons.add("evidence_sha_mismatch")
    if certification.evidence_bundle_hash != evidence.content_hash():
        reasons.add("certification_evidence_mismatch")
    if evidence.created_at > now or certification.issued_at > now:
        reasons.add("evidence_not_yet_valid")
    if not agent.enabled or agent.maturity not in {Maturity.CERTIFIED, Maturity.PRODUCTION_READY}:
        reasons.add("agent_not_certified_enabled")
    if now >= agent.expires_at:
        reasons.add("agent_expired")
    if not certification.is_active(now) or certification.subject_id != agent.agent_id:
        reasons.add("certification_inactive")
    if not lease.is_active(now):
        reasons.add("lease_inactive")
    if lease.agent_id != agent.agent_id or lease.certification_id != certification.certification_id:
        reasons.add("lease_identity_mismatch")
    lease_budget = lease.budget
    agent_budget = agent.budget
    if any(
        getattr(lease_budget, name) > getattr(agent_budget, name)
        for name in (
            "max_tokens",
            "max_seconds",
            "max_steps",
            "max_concurrency",
            "max_cost_microunits",
        )
    ):
        reasons.add("lease_budget_exceeds_agent")
    if (
        policy.policy_id != agent.policy_id
        or lease.policy_id != policy.policy_id
        or policy.tenant != agent.tenant
    ):
        reasons.add("policy_identity_mismatch")
    if tool.tenant != agent.tenant or evidence.tenant != agent.tenant:
        reasons.add("tenant_mismatch")
    if certification.tenant != agent.tenant or lease.tenant != agent.tenant:
        reasons.add("tenant_mismatch")
    if tool.tool_id not in agent.allowed_tool_ids or tool.tool_id in agent.forbidden_tool_ids:
        reasons.add("tool_not_allowed_for_agent")
    if capability not in agent.capabilities:
        reasons.add("capability_not_granted")
    if capability not in tool.capabilities:
        reasons.add("tool_capability_mismatch")
    if capability not in policy.allowed_capabilities or capability in policy.denied_capabilities:
        reasons.add("policy_denies_capability")
    if capability not in lease.granted_capabilities:
        reasons.add("lease_capability_mismatch")
    if not policy.deny_by_default:
        reasons.add("policy_not_deny_by_default")
    if not tool.enabled:
        reasons.add("tool_not_runtime_enabled")
    if tool.effect is not ToolEffect.READ_ONLY:
        reasons.add("mutating_tool_disabled_by_contract")
    if capability in policy.human_approval_capabilities:
        if approval is None:
            reasons.add("human_approval_required")
        elif not (
            approval.tenant == agent.tenant
            and approval.subject_id == agent.agent_id
            and approval.requester == agent.owner
            and approval.capability == capability
            and approval.evidence_bundle_hash == evidence.content_hash()
            and approval.decision is Decision.GO
            and approval.decided_at is not None
            and approval.requested_at <= approval.decided_at <= now < approval.expires_at
        ):
            reasons.add("human_approval_invalid")

    ordered_reasons = tuple(sorted(reasons))
    allowed = not ordered_reasons
    event = _event(
        now=now,
        agent=agent,
        tool=tool,
        capability=capability,
        commit_sha=evidence.commit_sha,
        allowed=allowed,
        reasons=ordered_reasons,
    )
    try:
        audit_sink.append(event)
    except Exception:
        failure_reasons = tuple(sorted((*reasons, "audit_unavailable")))
        failure_event = _event(
            now=now,
            agent=agent,
            tool=tool,
            capability=capability,
            commit_sha=evidence.commit_sha,
            allowed=False,
            reasons=failure_reasons,
        )
        return AdmissionDecision(False, failure_reasons, failure_event, False)
    return AdmissionDecision(allowed, ordered_reasons, event, True)

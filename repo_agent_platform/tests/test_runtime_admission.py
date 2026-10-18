from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from repo_agent_platform.contracts import (
    AgentManifest,
    ApprovalRequest,
    CertificationRecord,
    Decision,
    EvidenceBundle,
    EvidenceItem,
    ExecutionBudget,
    Maturity,
    PolicyManifest,
    RiskLevel,
    RuntimeLease,
    ToolEffect,
    ToolManifest,
)
from repo_agent_platform.core.runtime_admission import (
    AdmissionDecision,
    AuditEvent,
    AuditSink,
    admit_tool,
)

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)
EXPIRY = NOW + timedelta(hours=1)
HASH = "a" * 64
COMMIT = "b" * 40


class MemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)


def fixtures() -> tuple[
    AgentManifest, ToolManifest, PolicyManifest, EvidenceBundle, CertificationRecord, RuntimeLease
]:
    budget = ExecutionBudget(1000, 60, 10, 1, 10000)
    agent = AgentManifest(
        "agent.research",
        "tenant.one",
        "team.owner",
        "research",
        "1.0.0",
        ("public.web.read",),
        ("web.read",),
        ("shell.exec",),
        ("model.local",),
        "policy.research",
        "quality.research",
        RiskLevel.R1,
        budget,
        "sandbox.readonly",
        ("public",),
        EXPIRY,
        Maturity.CERTIFIED,
        True,
    )
    tool = ToolManifest(
        "web.read",
        "tenant.one",
        "team.tools",
        "1.0.0",
        ToolEffect.READ_ONLY,
        ("public.web.read",),
        HASH,
        HASH,
        10,
        enabled=True,
    )
    policy = PolicyManifest(
        "policy.research",
        "tenant.one",
        "team.security",
        "1.0.0",
        ("public.web.read",),
        ("shell.exec",),
        (),
    )
    evidence = EvidenceBundle(
        "bundle.research",
        "tenant.one",
        "team.owner",
        COMMIT,
        NOW,
        (EvidenceItem("ci", "https://example.invalid/run/1", HASH),),
        (),
        (),
        (),
    )
    certification = CertificationRecord(
        "cert.research",
        "agent.research",
        "tenant.one",
        "reviewer.one",
        evidence.content_hash(),
        NOW - timedelta(minutes=1),
        EXPIRY,
        Decision.GO,
    )
    lease = RuntimeLease(
        "lease.research",
        "tenant.one",
        "agent.research",
        "policy.research",
        "cert.research",
        ("public.web.read",),
        budget,
        NOW - timedelta(minutes=1),
        EXPIRY,
        HASH,
    )
    return agent, tool, policy, evidence, certification, lease


class RuntimeAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent, self.tool, self.policy, self.evidence, self.cert, self.lease = fixtures()
        self.audit = MemoryAuditSink()

    def admit(
        self,
        *,
        agent: AgentManifest | None = None,
        tool: ToolManifest | None = None,
        policy: PolicyManifest | None = None,
        evidence: EvidenceBundle | None = None,
        certification: CertificationRecord | None = None,
        lease: RuntimeLease | None = None,
        capability: str = "public.web.read",
        expected_commit_sha: str = COMMIT,
        now: datetime = NOW,
        audit_sink: AuditSink | None = None,
        approval: ApprovalRequest | None = None,
    ) -> AdmissionDecision:
        return admit_tool(
            agent=self.agent if agent is None else agent,
            tool=self.tool if tool is None else tool,
            policy=self.policy if policy is None else policy,
            evidence=self.evidence if evidence is None else evidence,
            certification=self.cert if certification is None else certification,
            lease=self.lease if lease is None else lease,
            capability=capability,
            expected_commit_sha=expected_commit_sha,
            now=now,
            audit_sink=self.audit if audit_sink is None else audit_sink,
            approval=approval,
        )

    def test_exact_sha_and_active_read_only_scope_is_admitted_and_audited(self) -> None:
        decision = self.admit()
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.audit_persisted)
        self.assertEqual(len(self.audit.events), 1)
        self.assertEqual(decision.audit_event.event_hash, self.audit.events[0].event_hash)
        self.assertEqual(
            hashlib.sha256(decision.audit_event.canonical_json().encode("utf-8")).hexdigest(),
            decision.audit_event.event_hash,
        )

    def test_wrong_commit_sha_is_denied(self) -> None:
        decision = self.admit(expected_commit_sha="c" * 40)
        self.assertFalse(decision.allowed)
        self.assertIn("evidence_sha_mismatch", decision.reason_codes)

    def test_expired_or_revoked_certification_is_denied(self) -> None:
        decision = self.admit(certification=replace(self.cert, revoked_at=NOW))
        self.assertFalse(decision.allowed)
        self.assertIn("certification_inactive", decision.reason_codes)
        future_cert = replace(self.cert, issued_at=NOW + timedelta(minutes=1))
        self.assertIn("evidence_not_yet_valid", self.admit(certification=future_cert).reason_codes)

    def test_scope_and_tenant_mismatch_are_denied(self) -> None:
        decision = self.admit(capability="public.web.write")
        self.assertFalse(decision.allowed)
        self.assertIn("capability_not_granted", decision.reason_codes)
        cross_tenant = replace(self.tool, tenant="tenant.two")
        self.assertFalse(self.admit(tool=cross_tenant).allowed)

    def test_lease_cannot_exceed_agent_execution_budget(self) -> None:
        larger_budget = ExecutionBudget(2000, 120, 20, 2, 20000)
        lease = replace(self.lease, budget=larger_budget)
        decision = self.admit(lease=lease)
        self.assertFalse(decision.allowed)
        self.assertIn("lease_budget_exceeds_agent", decision.reason_codes)

    def test_write_tool_remains_denied_even_with_matching_approval(self) -> None:
        write_tool = ToolManifest(
            "web.write",
            "tenant.one",
            "team.tools",
            "1.0.0",
            ToolEffect.WRITE_SCOPED,
            ("public.web.write",),
            HASH,
            HASH,
            10,
        )
        policy = replace(
            self.policy,
            allowed_capabilities=("public.web.read", "public.web.write"),
            human_approval_capabilities=("public.web.write",),
        )
        decision = self.admit(tool=write_tool, policy=policy, capability="public.web.write")
        self.assertFalse(decision.allowed)
        self.assertIn("tool_not_runtime_enabled", decision.reason_codes)

    def test_sensitive_capability_requires_exact_current_approval(self) -> None:
        capability = "public.web.read"
        policy = replace(self.policy, human_approval_capabilities=(capability,))
        denied = self.admit(policy=policy)
        self.assertIn("human_approval_required", denied.reason_codes)
        approval = ApprovalRequest(
            "approval.research",
            "tenant.one",
            "team.owner",
            "reviewer.one",
            capability,
            "agent.research",
            self.evidence.content_hash(),
            NOW - timedelta(minutes=1),
            EXPIRY,
            Decision.GO,
            NOW,
        )
        self.assertTrue(self.admit(policy=policy, approval=approval).allowed)
        wrong_subject = replace(approval, subject_id="agent.other")
        self.assertIn(
            "human_approval_invalid",
            self.admit(policy=policy, approval=wrong_subject).reason_codes,
        )

    def test_audit_failure_prevents_admission(self) -> None:
        class FailingSink:
            def append(self, event: AuditEvent) -> None:
                raise OSError("audit unavailable")

        result = self.admit(audit_sink=FailingSink())
        self.assertFalse(result.allowed)
        self.assertFalse(result.audit_persisted)
        self.assertIn("audit_unavailable", result.reason_codes)

    def test_audit_event_contains_no_tool_input(self) -> None:
        decision = self.admit()
        self.assertNotIn("secret", decision.audit_event.canonical_json())
        self.assertEqual(decision.audit_event.commit_sha, COMMIT)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

from repo_agent_platform.contracts import (
    AgentManifest,
    ApprovalRequest,
    CertificationRecord,
    ContractError,
    Decision,
    EvidenceBundle,
    EvidenceItem,
    ExecutionBudget,
    MCPServerManifest,
    Maturity,
    ModelManifest,
    PolicyManifest,
    QualityContract,
    RiskLevel,
    RuntimeLease,
    ToolEffect,
    ToolManifest,
)

NOW = datetime(2026, 7, 25, 18, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)
HASH = "a" * 64
COMMIT = "b" * 40


def budget() -> ExecutionBudget:
    return ExecutionBudget(10_000, 60, 20, 2, 1_000_000)


def evidence_bundle() -> EvidenceBundle:
    return EvidenceBundle(
        "bundle.pr10",
        "tenant.one",
        "platform.team",
        COMMIT,
        NOW,
        (EvidenceItem("ci", "github://run/10", HASH),),
        (),
        ("contract.validation.changed",),
        ("registry.not.implemented",),
    )


class EnterpriseContractTests(unittest.TestCase):
    def test_budget_is_strict_immutable_and_hashable(self) -> None:
        value = budget()
        self.assertEqual(len(value.content_hash()), 64)
        self.assertIn('"max_steps":20', value.canonical_json())
        with self.assertRaises(FrozenInstanceError):
            value.max_steps = 99  # type: ignore[misc]
        with self.assertRaises(ContractError):
            ExecutionBudget(0, 1, 1, 1, 0)
        with self.assertRaises(ContractError):
            ExecutionBudget(1, 1, 1, 1, -1)

    def test_quality_contract_preserves_human_gate(self) -> None:
        contract = QualityContract("quality.research", "platform.team", ("groundedness",), 9500)
        self.assertTrue(contract.human_approval_required)
        with self.assertRaises(ContractError):
            QualityContract("quality.research", "platform.team", ("groundedness",), 9500, 1)
        with self.assertRaises(ContractError):
            QualityContract(
                "quality.research",
                "platform.team",
                ("groundedness",),
                9500,
                human_approval_required=False,
            )

    def test_tool_manifest_rejects_global_or_enabled_write_access(self) -> None:
        tool = ToolManifest(
            "web.read",
            "tenant.one",
            "platform.team",
            "1.0.0",
            ToolEffect.READ_ONLY,
            ("public.web.read",),
            HASH,
            HASH,
            15,
        )
        self.assertFalse(tool.enabled)
        with self.assertRaises(ContractError):
            ToolManifest(
                "shell",
                "tenant.one",
                "platform.team",
                "1.0.0",
                ToolEffect.READ_ONLY,
                ("shell.*",),
                HASH,
                HASH,
                15,
            )
        with self.assertRaises(ContractError):
            ToolManifest(
                "github.write",
                "tenant.one",
                "platform.team",
                "1.0.0",
                ToolEffect.WRITE_SCOPED,
                ("github.pr.write",),
                HASH,
                HASH,
                15,
                enabled=True,
            )

    def test_model_manifest_blocks_silent_fallback(self) -> None:
        with self.assertRaises(ContractError):
            ModelManifest(
                "model.primary",
                "provider.approved",
                "ai.team",
                "1.0.0",
                ("research",),
                128_000,
                ("public",),
                ("model.primary",),
            )
        with self.assertRaises(ContractError):
            ModelManifest(
                "model.primary",
                "provider.approved",
                "ai.team",
                "1.0.0",
                ("research",),
                128_000,
                ("public",),
                ("model.secondary",),
                enabled=True,
            )

    def test_policy_is_exact_match_and_deny_by_default(self) -> None:
        policy = PolicyManifest(
            "policy.research",
            "tenant.one",
            "security.team",
            "1.0.0",
            ("public.web.read",),
            ("github.write", "shell.unrestricted"),
            ("artifact.publish",),
        )
        self.assertTrue(policy.permits("public.web.read"))
        self.assertFalse(policy.permits("public.web"))
        self.assertFalse(policy.permits("github.write"))
        with self.assertRaises(ContractError):
            PolicyManifest(
                "policy.research",
                "tenant.one",
                "security.team",
                "1.0.0",
                (),
                ("github.write",),
                (),
                deny_by_default=False,
            )
        with self.assertRaises(ContractError):
            PolicyManifest(
                "policy.research",
                "tenant.one",
                "security.team",
                "1.0.0",
                ("public.web.read",),
                ("public.web.read",),
                (),
            )

    def test_agent_requires_certification_before_enablement(self) -> None:
        agent = AgentManifest(
            "agent.research",
            "tenant.one",
            "agent.team",
            "researcher",
            "1.0.0",
            ("public.web.read",),
            (),
            ("shell.unrestricted", "github.write"),
            ("model.primary",),
            "policy.research",
            "quality.research",
            RiskLevel.R2,
            budget(),
            "sandbox.readonly",
            ("public",),
            LATER,
        )
        self.assertIs(agent.maturity, Maturity.PROPOSED)
        with self.assertRaises(ContractError):
            AgentManifest(
                "agent.research",
                "tenant.one",
                "agent.team",
                "researcher",
                "1.0.0",
                ("public.web.read",),
                (),
                ("github.write",),
                ("model.primary",),
                "policy.research",
                "quality.research",
                RiskLevel.R2,
                budget(),
                "sandbox.readonly",
                ("public",),
                LATER,
                enabled=True,
            )

    def test_agent_rejects_tool_conflict_and_naive_expiry(self) -> None:
        common = {
            "agent_id": "agent.research",
            "tenant": "tenant.one",
            "owner": "agent.team",
            "role": "researcher",
            "version": "1.0.0",
            "capabilities": ("public.web.read",),
            "model_ids": ("model.primary",),
            "policy_id": "policy.research",
            "quality_contract_id": "quality.research",
            "risk_level": RiskLevel.R2,
            "budget": budget(),
            "sandbox_profile": "sandbox.readonly",
            "data_classifications": ("public",),
        }
        with self.assertRaises(ContractError):
            AgentManifest(
                **common,
                allowed_tool_ids=("web.read",),
                forbidden_tool_ids=("web.read",),
                expires_at=LATER,
            )
        with self.assertRaises(ContractError):
            AgentManifest(
                **common,
                allowed_tool_ids=(),
                forbidden_tool_ids=("github.write",),
                expires_at=datetime(2026, 7, 25),
            )

    def test_mcp_remains_read_only_and_disabled(self) -> None:
        server = MCPServerManifest(
            "mcp.research",
            "tenant.one",
            "platform.team",
            "1.0.0",
            ("web.read",),
            "stdio",
            "identity.research",
            20,
        )
        self.assertTrue(server.read_only)
        self.assertFalse(server.enabled)
        with self.assertRaises(ContractError):
            MCPServerManifest(
                "mcp.research",
                "tenant.one",
                "platform.team",
                "1.0.0",
                ("web.read",),
                "stdio",
                "identity.research",
                20,
                read_only=False,
            )

    def test_evidence_is_commit_bound_and_nonempty(self) -> None:
        bundle = evidence_bundle()
        self.assertEqual(len(bundle.content_hash()), 64)
        with self.assertRaises(ContractError):
            EvidenceBundle(
                "bundle.pr10",
                "tenant.one",
                "platform.team",
                "short",
                NOW,
                (EvidenceItem("ci", "github://run/10", HASH),),
                (),
                (),
                (),
            )
        with self.assertRaises(ContractError):
            EvidenceBundle(
                "bundle.pr10",
                "tenant.one",
                "platform.team",
                COMMIT,
                NOW,
                (),
                (),
                (),
                (),
            )

    def test_certification_has_ttl_and_revocation(self) -> None:
        record = CertificationRecord(
            "cert.agent.research",
            "agent.research",
            "tenant.one",
            "reviewer.one",
            evidence_bundle().content_hash(),
            NOW,
            LATER,
            Decision.GO,
        )
        self.assertTrue(record.is_active(NOW + timedelta(minutes=1)))
        self.assertFalse(record.is_active(LATER))
        revoked = CertificationRecord(
            "cert.agent.research",
            "agent.research",
            "tenant.one",
            "reviewer.one",
            evidence_bundle().content_hash(),
            NOW,
            LATER,
            Decision.GO,
            NOW + timedelta(minutes=2),
        )
        self.assertFalse(revoked.is_active(NOW + timedelta(minutes=3)))

    def test_runtime_lease_is_bounded_and_scoped(self) -> None:
        lease = RuntimeLease(
            "lease.research.1",
            "tenant.one",
            "agent.research",
            "policy.research",
            "cert.agent.research",
            ("public.web.read",),
            budget(),
            NOW,
            LATER,
            HASH,
        )
        self.assertTrue(lease.is_active(NOW))
        self.assertFalse(lease.is_active(LATER))
        with self.assertRaises(ContractError):
            RuntimeLease(
                "lease.research.1",
                "tenant.one",
                "agent.research",
                "policy.research",
                "cert.agent.research",
                ("*",),
                budget(),
                NOW,
                LATER,
                HASH,
            )

    def test_approval_enforces_separation_and_conditions(self) -> None:
        request = ApprovalRequest(
            "approval.research.1",
            "tenant.one",
            "requester.one",
            "reviewer.one",
            "public.web.read",
            "agent.research",
            evidence_bundle().content_hash(),
            NOW,
            LATER,
        )
        approved = request.with_decision(decision=Decision.GO, decided_at=NOW)
        self.assertIs(approved.decision, Decision.GO)
        with self.assertRaises(ContractError):
            ApprovalRequest(
                "approval.research.1",
                "tenant.one",
                "same.identity",
                "same.identity",
                "public.web.read",
                "agent.research",
                HASH,
                NOW,
                LATER,
            )
        with self.assertRaises(ContractError):
            request.with_decision(decision=Decision.CONDITIONAL_GO, decided_at=NOW)

    def test_identifiers_and_versions_fail_closed(self) -> None:
        for bad_id in ("", "UPPER", "has space", "../escape", "a/*"):
            with self.subTest(bad_id=bad_id), self.assertRaises(ContractError):
                QualityContract(bad_id, "platform.team", ("groundedness",), 9500)
        for version in ("1", "1.0", "v1.0.0", "01.0.0", "1.0.0-beta"):
            with self.subTest(version=version), self.assertRaises(ContractError):
                ToolManifest(
                    "web.read",
                    "tenant.one",
                    "platform.team",
                    version,
                    ToolEffect.READ_ONLY,
                    ("public.web.read",),
                    HASH,
                    HASH,
                    15,
                )


if __name__ == "__main__":
    unittest.main()

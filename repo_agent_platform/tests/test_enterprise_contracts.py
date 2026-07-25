from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

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


def test_budget_is_strict_immutable_and_hashable() -> None:
    value = budget()
    assert len(value.content_hash()) == 64
    assert '"max_steps":20' in value.canonical_json()
    with pytest.raises(FrozenInstanceError):
        value.max_steps = 99  # type: ignore[misc]
    with pytest.raises(ContractError):
        ExecutionBudget(0, 1, 1, 1, 0)
    with pytest.raises(ContractError):
        ExecutionBudget(1, 1, 1, 1, -1)


def test_quality_contract_enforces_human_gate_and_zero_critical_findings() -> None:
    contract = QualityContract("quality.research", "platform.team", ("groundedness",), 9500)
    assert contract.human_approval_required
    with pytest.raises(ContractError):
        QualityContract("quality.research", "platform.team", ("groundedness",), 9500, 1)
    with pytest.raises(ContractError):
        QualityContract(
            "quality.research",
            "platform.team",
            ("groundedness",),
            9500,
            human_approval_required=False,
        )


def test_tool_manifest_rejects_global_grants_and_enabled_write_tool() -> None:
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
    assert not tool.enabled
    with pytest.raises(ContractError):
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
    with pytest.raises(ContractError):
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


def test_model_manifest_blocks_silent_fallback() -> None:
    model = ModelManifest(
        "model.primary",
        "provider.approved",
        "ai.team",
        "1.0.0",
        ("research",),
        128_000,
        ("public",),
    )
    assert not model.enabled
    with pytest.raises(ContractError):
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
    with pytest.raises(ContractError):
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


def test_policy_is_deny_by_default_and_exact_match_only() -> None:
    policy = PolicyManifest(
        "policy.research",
        "tenant.one",
        "security.team",
        "1.0.0",
        ("public.web.read",),
        ("github.write", "shell.unrestricted"),
        ("artifact.publish",),
    )
    assert policy.permits("public.web.read")
    assert not policy.permits("public.web")
    assert not policy.permits("github.write")
    with pytest.raises(ContractError):
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
    with pytest.raises(ContractError):
        PolicyManifest(
            "policy.research",
            "tenant.one",
            "security.team",
            "1.0.0",
            ("public.web.read",),
            ("public.web.read",),
            (),
        )


def test_agent_manifest_requires_certification_before_enablement() -> None:
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
    assert agent.maturity is Maturity.PROPOSED
    with pytest.raises(ContractError):
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


def test_agent_manifest_rejects_tool_conflict_and_naive_expiry() -> None:
    common = dict(
        agent_id="agent.research",
        tenant="tenant.one",
        owner="agent.team",
        role="researcher",
        version="1.0.0",
        capabilities=("public.web.read",),
        model_ids=("model.primary",),
        policy_id="policy.research",
        quality_contract_id="quality.research",
        risk_level=RiskLevel.R2,
        budget=budget(),
        sandbox_profile="sandbox.readonly",
        data_classifications=("public",),
    )
    with pytest.raises(ContractError):
        AgentManifest(
            **common,
            allowed_tool_ids=("web.read",),
            forbidden_tool_ids=("web.read",),
            expires_at=LATER,
        )
    with pytest.raises(ContractError):
        AgentManifest(
            **common,
            allowed_tool_ids=(),
            forbidden_tool_ids=("github.write",),
            expires_at=datetime(2026, 7, 25),
        )


def test_mcp_contract_is_read_only_and_disabled() -> None:
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
    assert server.read_only and not server.enabled
    with pytest.raises(ContractError):
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


def test_evidence_bundle_is_immutable_and_commit_bound() -> None:
    bundle = evidence_bundle()
    assert len(bundle.content_hash()) == 64
    with pytest.raises(ContractError):
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
    with pytest.raises(ContractError):
        EvidenceBundle("bundle.pr10", "tenant.one", "platform.team", COMMIT, NOW, (), (), (), ())


def test_certification_has_ttl_revocation_and_go_semantics() -> None:
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
    assert record.is_active(NOW + timedelta(minutes=1))
    assert not record.is_active(LATER)
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
    assert not revoked.is_active(NOW + timedelta(minutes=3))
    with pytest.raises(ContractError):
        CertificationRecord(
            "cert.agent.research",
            "agent.research",
            "tenant.one",
            "reviewer.one",
            HASH,
            NOW,
            NOW,
            Decision.GO,
        )


def test_runtime_lease_is_bounded_revocable_and_scoped() -> None:
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
    assert lease.is_active(NOW)
    assert not lease.is_active(LATER)
    with pytest.raises(ContractError):
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


def test_approval_enforces_separation_ttl_and_conditions() -> None:
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
    assert approved.decision is Decision.GO
    with pytest.raises(ContractError):
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
    with pytest.raises(ContractError):
        request.with_decision(decision=Decision.CONDITIONAL_GO, decided_at=NOW)
    conditional = request.with_decision(
        decision=Decision.CONDITIONAL_GO,
        decided_at=NOW,
        conditions=("read.only",),
    )
    assert conditional.conditions == ("read.only",)


@pytest.mark.parametrize("bad_id", ["", "UPPER", "has space", "../escape", "a/*"])
def test_identifiers_fail_closed(bad_id: str) -> None:
    with pytest.raises(ContractError):
        QualityContract(bad_id, "platform.team", ("groundedness",), 9500)


@pytest.mark.parametrize("version", ["1", "1.0", "v1.0.0", "01.0.0", "1.0.0-beta"])
def test_versions_are_strict_semver(version: str) -> None:
    with pytest.raises(ContractError):
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

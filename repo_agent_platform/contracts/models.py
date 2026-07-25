from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_FORBIDDEN_GLOBAL_TOKENS = {"*", "all", "global", "unrestricted"}


class ContractError(ValueError):
    """Raised when a contract violates a fail-closed invariant."""


class Maturity(StrEnum):
    PROPOSED = "PROPOSED"
    ADR_APPROVED = "ADR_APPROVED"
    IMPLEMENTING = "IMPLEMENTING"
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    CERTIFIED = "CERTIFIED"
    PRODUCTION_READY = "PRODUCTION_READY"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class RiskLevel(StrEnum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"


class Decision(StrEnum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    NO_GO = "NO_GO"


class ToolEffect(StrEnum):
    READ_ONLY = "READ_ONLY"
    WRITE_SCOPED = "WRITE_SCOPED"
    DESTRUCTIVE = "DESTRUCTIVE"


class ContractMixin:
    schema_version: str

    def canonical_json(self) -> str:
        return json.dumps(
            asdict(self),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=_json_default,
        )

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, StrEnum):
        return str(value)
    raise TypeError(f"Unsupported canonical value: {type(value).__name__}")


def _require_identifier(name: str, value: str) -> None:
    if not _ID_PATTERN.fullmatch(value):
        raise ContractError(f"{name} must be a canonical identifier")


def _require_semver(value: str) -> None:
    if not _SEMVER_PATTERN.fullmatch(value):
        raise ContractError("version must use strict MAJOR.MINOR.PATCH")


def _require_utc(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ContractError(f"{name} must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ContractError(f"{name} must be expressed in UTC")


def _require_nonempty(name: str, values: tuple[str, ...]) -> None:
    if not values or any(not value.strip() for value in values):
        raise ContractError(f"{name} must contain non-empty values")


def _require_scoped(name: str, values: tuple[str, ...]) -> None:
    for value in values:
        lowered = value.lower()
        if lowered in _FORBIDDEN_GLOBAL_TOKENS or any(
            token in lowered for token in ("unrestricted", "global.*", "shell.*", "filesystem.*")
        ):
            raise ContractError(f"{name} contains a global or unrestricted grant: {value}")


@dataclass(frozen=True, slots=True)
class ExecutionBudget(ContractMixin):
    max_tokens: int
    max_seconds: int
    max_steps: int
    max_concurrency: int
    max_cost_microunits: int
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _require_semver(self.schema_version)
        limits = (
            self.max_tokens,
            self.max_seconds,
            self.max_steps,
            self.max_concurrency,
        )
        if any(value <= 0 for value in limits):
            raise ContractError("execution limits must be positive")
        if self.max_cost_microunits < 0:
            raise ContractError("cost budget cannot be negative")


@dataclass(frozen=True, slots=True)
class QualityContract(ContractMixin):
    contract_id: str
    owner: str
    required_evaluations: tuple[str, ...]
    min_pass_rate_basis_points: int
    max_critical_findings: int = 0
    human_approval_required: bool = True
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _require_identifier("contract_id", self.contract_id)
        _require_identifier("owner", self.owner)
        _require_nonempty("required_evaluations", self.required_evaluations)
        _require_scoped("required_evaluations", self.required_evaluations)
        if not 0 <= self.min_pass_rate_basis_points <= 10_000:
            raise ContractError("pass rate must be between 0 and 10000 basis points")
        if self.max_critical_findings != 0:
            raise ContractError("critical findings allowance must remain zero")
        if not self.human_approval_required:
            raise ContractError("human approval cannot be disabled")


@dataclass(frozen=True, slots=True)
class ToolManifest(ContractMixin):
    tool_id: str
    tenant: str
    owner: str
    version: str
    effect: ToolEffect
    capabilities: tuple[str, ...]
    input_schema_hash: str
    output_schema_hash: str
    timeout_seconds: int
    egress_allowlist: tuple[str, ...] = ()
    enabled: bool = False
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name, value in (("tool_id", self.tool_id), ("tenant", self.tenant), ("owner", self.owner)):
            _require_identifier(name, value)
        _require_semver(self.version)
        _require_nonempty("capabilities", self.capabilities)
        _require_scoped("capabilities", self.capabilities)
        if not _SHA256_PATTERN.fullmatch(self.input_schema_hash):
            raise ContractError("input_schema_hash must be SHA-256")
        if not _SHA256_PATTERN.fullmatch(self.output_schema_hash):
            raise ContractError("output_schema_hash must be SHA-256")
        if self.timeout_seconds <= 0:
            raise ContractError("timeout_seconds must be positive")
        if self.effect is not ToolEffect.READ_ONLY and self.enabled:
            raise ContractError("non-read-only tools cannot be enabled by manifest alone")


@dataclass(frozen=True, slots=True)
class ModelManifest(ContractMixin):
    model_id: str
    provider: str
    owner: str
    version: str
    allowed_purposes: tuple[str, ...]
    max_context_tokens: int
    data_classifications: tuple[str, ...]
    fallback_model_ids: tuple[str, ...] = ()
    enabled: bool = False
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name, value in (("model_id", self.model_id), ("provider", self.provider), ("owner", self.owner)):
            _require_identifier(name, value)
        _require_semver(self.version)
        _require_nonempty("allowed_purposes", self.allowed_purposes)
        _require_scoped("allowed_purposes", self.allowed_purposes)
        _require_nonempty("data_classifications", self.data_classifications)
        if self.max_context_tokens <= 0:
            raise ContractError("max_context_tokens must be positive")
        if self.model_id in self.fallback_model_ids:
            raise ContractError("a model cannot fall back to itself")
        if self.fallback_model_ids and self.enabled:
            raise ContractError("fallback requires a separate policy decision")


@dataclass(frozen=True, slots=True)
class PolicyManifest(ContractMixin):
    policy_id: str
    tenant: str
    owner: str
    version: str
    allowed_capabilities: tuple[str, ...]
    denied_capabilities: tuple[str, ...]
    human_approval_capabilities: tuple[str, ...]
    deny_by_default: bool = True
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name, value in (("policy_id", self.policy_id), ("tenant", self.tenant), ("owner", self.owner)):
            _require_identifier(name, value)
        _require_semver(self.version)
        _require_nonempty("denied_capabilities", self.denied_capabilities)
        _require_scoped("allowed_capabilities", self.allowed_capabilities)
        _require_scoped("denied_capabilities", self.denied_capabilities)
        _require_scoped("human_approval_capabilities", self.human_approval_capabilities)
        if not self.deny_by_default:
            raise ContractError("deny_by_default cannot be disabled")
        overlap = set(self.allowed_capabilities) & set(self.denied_capabilities)
        if overlap:
            raise ContractError(f"capabilities cannot be both allowed and denied: {sorted(overlap)}")

    def permits(self, capability: str) -> bool:
        return capability in self.allowed_capabilities and capability not in self.denied_capabilities


@dataclass(frozen=True, slots=True)
class AgentManifest(ContractMixin):
    agent_id: str
    tenant: str
    owner: str
    role: str
    version: str
    capabilities: tuple[str, ...]
    allowed_tool_ids: tuple[str, ...]
    forbidden_tool_ids: tuple[str, ...]
    model_ids: tuple[str, ...]
    policy_id: str
    quality_contract_id: str
    risk_level: RiskLevel
    budget: ExecutionBudget
    sandbox_profile: str
    data_classifications: tuple[str, ...]
    expires_at: datetime
    maturity: Maturity = Maturity.PROPOSED
    enabled: bool = False
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        identifiers = (
            ("agent_id", self.agent_id),
            ("tenant", self.tenant),
            ("owner", self.owner),
            ("role", self.role),
            ("policy_id", self.policy_id),
            ("quality_contract_id", self.quality_contract_id),
            ("sandbox_profile", self.sandbox_profile),
        )
        for name, value in identifiers:
            _require_identifier(name, value)
        _require_semver(self.version)
        _require_nonempty("capabilities", self.capabilities)
        _require_scoped("capabilities", self.capabilities)
        _require_scoped("allowed_tool_ids", self.allowed_tool_ids)
        _require_nonempty("forbidden_tool_ids", self.forbidden_tool_ids)
        _require_scoped("forbidden_tool_ids", self.forbidden_tool_ids)
        _require_nonempty("model_ids", self.model_ids)
        _require_nonempty("data_classifications", self.data_classifications)
        _require_utc("expires_at", self.expires_at)
        overlap = set(self.allowed_tool_ids) & set(self.forbidden_tool_ids)
        if overlap:
            raise ContractError(f"tools cannot be both allowed and forbidden: {sorted(overlap)}")
        if self.enabled and self.maturity not in {Maturity.CERTIFIED, Maturity.PRODUCTION_READY}:
            raise ContractError("only certified manifests can be enabled")


@dataclass(frozen=True, slots=True)
class MCPServerManifest(ContractMixin):
    server_id: str
    tenant: str
    owner: str
    version: str
    tool_ids: tuple[str, ...]
    transport: str
    endpoint_identity: str
    timeout_seconds: int
    read_only: bool = True
    enabled: bool = False
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name, value in (("server_id", self.server_id), ("tenant", self.tenant), ("owner", self.owner)):
            _require_identifier(name, value)
        _require_semver(self.version)
        _require_nonempty("tool_ids", self.tool_ids)
        _require_scoped("tool_ids", self.tool_ids)
        _require_identifier("transport", self.transport)
        _require_identifier("endpoint_identity", self.endpoint_identity)
        if self.timeout_seconds <= 0:
            raise ContractError("timeout_seconds must be positive")
        if not self.read_only or self.enabled:
            raise ContractError("MCP remains disabled and read-only in this increment")


@dataclass(frozen=True, slots=True)
class EvidenceItem(ContractMixin):
    evidence_type: str
    uri: str
    sha256: str
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _require_identifier("evidence_type", self.evidence_type)
        if not self.uri.strip():
            raise ContractError("evidence URI cannot be empty")
        if not _SHA256_PATTERN.fullmatch(self.sha256):
            raise ContractError("evidence hash must be SHA-256")


@dataclass(frozen=True, slots=True)
class EvidenceBundle(ContractMixin):
    bundle_id: str
    tenant: str
    owner: str
    commit_sha: str
    created_at: datetime
    items: tuple[EvidenceItem, ...]
    permission_diff: tuple[str, ...]
    behavior_diff: tuple[str, ...]
    residual_risks: tuple[str, ...]
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name, value in (("bundle_id", self.bundle_id), ("tenant", self.tenant), ("owner", self.owner)):
            _require_identifier(name, value)
        if not re.fullmatch(r"^[0-9a-f]{40}$", self.commit_sha):
            raise ContractError("commit_sha must be an immutable 40-character SHA")
        _require_utc("created_at", self.created_at)
        if not self.items:
            raise ContractError("evidence bundle cannot be empty")


@dataclass(frozen=True, slots=True)
class CertificationRecord(ContractMixin):
    certification_id: str
    subject_id: str
    tenant: str
    approver: str
    evidence_bundle_hash: str
    issued_at: datetime
    expires_at: datetime
    decision: Decision
    revoked_at: datetime | None = None
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name, value in (
            ("certification_id", self.certification_id),
            ("subject_id", self.subject_id),
            ("tenant", self.tenant),
            ("approver", self.approver),
        ):
            _require_identifier(name, value)
        if not _SHA256_PATTERN.fullmatch(self.evidence_bundle_hash):
            raise ContractError("evidence_bundle_hash must be SHA-256")
        _require_utc("issued_at", self.issued_at)
        _require_utc("expires_at", self.expires_at)
        if self.expires_at <= self.issued_at:
            raise ContractError("certification must expire after issuance")
        if self.revoked_at is not None:
            _require_utc("revoked_at", self.revoked_at)
            if self.revoked_at < self.issued_at:
                raise ContractError("revocation cannot predate issuance")

    def is_active(self, now: datetime) -> bool:
        _require_utc("now", now)
        return self.decision is Decision.GO and self.revoked_at is None and now < self.expires_at


@dataclass(frozen=True, slots=True)
class RuntimeLease(ContractMixin):
    lease_id: str
    tenant: str
    agent_id: str
    policy_id: str
    certification_id: str
    granted_capabilities: tuple[str, ...]
    budget: ExecutionBudget
    issued_at: datetime
    expires_at: datetime
    kill_switch_token_hash: str
    revoked_at: datetime | None = None
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name, value in (
            ("lease_id", self.lease_id),
            ("tenant", self.tenant),
            ("agent_id", self.agent_id),
            ("policy_id", self.policy_id),
            ("certification_id", self.certification_id),
        ):
            _require_identifier(name, value)
        _require_nonempty("granted_capabilities", self.granted_capabilities)
        _require_scoped("granted_capabilities", self.granted_capabilities)
        _require_utc("issued_at", self.issued_at)
        _require_utc("expires_at", self.expires_at)
        if self.expires_at <= self.issued_at:
            raise ContractError("lease must expire after issuance")
        if not _SHA256_PATTERN.fullmatch(self.kill_switch_token_hash):
            raise ContractError("kill switch token must be stored as SHA-256")
        if self.revoked_at is not None:
            _require_utc("revoked_at", self.revoked_at)

    def is_active(self, now: datetime) -> bool:
        _require_utc("now", now)
        return self.revoked_at is None and self.issued_at <= now < self.expires_at


@dataclass(frozen=True, slots=True)
class ApprovalRequest(ContractMixin):
    request_id: str
    tenant: str
    requester: str
    approver: str
    capability: str
    subject_id: str
    evidence_bundle_hash: str
    requested_at: datetime
    expires_at: datetime
    decision: Decision = Decision.NO_GO
    decided_at: datetime | None = None
    conditions: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name, value in (
            ("request_id", self.request_id),
            ("tenant", self.tenant),
            ("requester", self.requester),
            ("approver", self.approver),
            ("subject_id", self.subject_id),
        ):
            _require_identifier(name, value)
        _require_scoped("capability", (self.capability,))
        if self.requester == self.approver:
            raise ContractError("requester and approver must be different identities")
        if not _SHA256_PATTERN.fullmatch(self.evidence_bundle_hash):
            raise ContractError("evidence_bundle_hash must be SHA-256")
        _require_utc("requested_at", self.requested_at)
        _require_utc("expires_at", self.expires_at)
        if self.expires_at <= self.requested_at:
            raise ContractError("approval request must expire after creation")
        if self.decided_at is not None:
            _require_utc("decided_at", self.decided_at)
            if self.decided_at < self.requested_at:
                raise ContractError("decision cannot predate request")
        if self.decision is Decision.CONDITIONAL_GO and not self.conditions:
            raise ContractError("conditional approval requires explicit conditions")

    def with_decision(
        self,
        *,
        decision: Decision,
        decided_at: datetime,
        conditions: tuple[str, ...] = (),
    ) -> Self:
        return type(self)(
            request_id=self.request_id,
            tenant=self.tenant,
            requester=self.requester,
            approver=self.approver,
            capability=self.capability,
            subject_id=self.subject_id,
            evidence_bundle_hash=self.evidence_bundle_hash,
            requested_at=self.requested_at,
            expires_at=self.expires_at,
            decision=decision,
            decided_at=decided_at,
            conditions=conditions,
            schema_version=self.schema_version,
        )

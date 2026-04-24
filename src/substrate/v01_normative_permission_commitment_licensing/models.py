from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class V01ActType(str, Enum):
    ASSERTION = "assertion"
    ADVICE = "advice"
    PROMISE = "promise"
    REFUSAL = "refusal"
    WARNING = "warning"
    QUESTION = "question"
    REQUEST = "request"
    ACKNOWLEDGEMENT = "acknowledgement"
    BOUNDARY_STATEMENT = "boundary_statement"
    EXPLANATION = "explanation"


class V01CommitmentDeltaKind(str, Enum):
    CREATE_COMMITMENT = "create_commitment"
    COMMITMENT_DENIED = "commitment_denied"
    NO_COMMITMENT_CHANGE = "no_commitment_change"


@dataclass(frozen=True, slots=True)
class V01CommunicativeActCandidate:
    act_id: str
    act_type: V01ActType = V01ActType.EXPLANATION
    proposition_ref: str = ""
    evidence_strength: float = 0.0
    authority_basis_present: bool = False
    explicit_uncertainty_present: bool = False
    helpfulness_pressure: float = 0.0
    protective_sensitivity: bool = False
    commitment_target_ref: str | None = None
    provenance: str = "v01.communicative_act_candidate"


@dataclass(frozen=True, slots=True)
class V01LicensedActEntry:
    act_id: str
    act_type: V01ActType
    conditional_license: bool
    mandatory_qualifiers: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class V01DeniedActEntry:
    act_id: str
    act_type: V01ActType
    deny_reason: str
    blocking_reason_code: str
    alternative_narrowed_act_type: V01ActType | None = None


@dataclass(frozen=True, slots=True)
class V01CommitmentDelta:
    act_id: str
    act_type: V01ActType
    delta_kind: V01CommitmentDeltaKind
    commitment_target_ref: str | None
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class V01CommunicativeLicenseState:
    license_id: str
    candidate_act_count: int
    licensed_acts: tuple[V01LicensedActEntry, ...]
    denied_acts: tuple[V01DeniedActEntry, ...]
    commitment_deltas: tuple[V01CommitmentDelta, ...]
    mandatory_qualifiers: tuple[str, ...]
    licensed_act_count: int
    denied_act_count: int
    conditional_act_count: int
    commitment_delta_count: int
    mandatory_qualifier_count: int
    protective_defer_required: bool
    insufficient_license_basis: bool
    qualification_required: bool
    assertion_allowed_commitment_denied: bool
    clarification_before_commitment: bool
    cannot_license_advice: bool
    promise_like_act_denied: bool
    alternative_narrowed_act_available: bool
    justification_links: tuple[str, ...]
    provenance: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class V01LicenseGateDecision:
    license_consumer_ready: bool
    commitment_delta_consumer_ready: bool
    qualifier_binding_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class V01ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    v01_first_slice_only: bool
    v02_not_implemented: bool
    v03_not_implemented: bool
    p02_not_implemented: bool
    p04_not_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class V01Telemetry:
    license_id: str
    tick_index: int
    candidate_act_count: int
    licensed_act_count: int
    denied_act_count: int
    conditional_act_count: int
    commitment_delta_count: int
    mandatory_qualifier_count: int
    protective_defer_required: bool
    insufficient_license_basis: bool
    downstream_consumer_ready: bool
    promise_like_act_denied: bool
    alternative_narrowed_act_available: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class V01LicenseResult:
    state: V01CommunicativeLicenseState
    gate: V01LicenseGateDecision
    scope_marker: V01ScopeMarker
    telemetry: V01Telemetry
    reason: str

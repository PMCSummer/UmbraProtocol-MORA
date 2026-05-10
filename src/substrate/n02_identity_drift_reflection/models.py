from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class N02IdentityRegionKind(str, Enum):
    SELF_DESCRIPTION = "self_description"
    CAPABILITY_CONTOUR = "capability_contour"
    LIMITATION_CONTOUR = "limitation_contour"
    RELATION_STANCE = "relation_stance"
    VALUE_LIKE_STANCE = "value_like_stance"
    SELF_BINDING_CORE = "self_binding_core"
    AFFORDANCE_PROFILE = "affordance_profile"
    COMMITMENT_PATTERN = "commitment_pattern"
    MIXED_IDENTITY_REGION = "mixed_identity_region"
    UNKNOWN = "unknown"


class N02DriftKind(str, Enum):
    STABLE_CONTINUATION = "stable_continuation"
    BOUNDED_REVISION = "bounded_revision"
    GRADUAL_SHIFT = "gradual_shift"
    ABRUPT_REORIENTATION = "abrupt_reorientation"
    CONTEXT_SPLIT_DETECTED = "context_split_detected"
    COMMITMENT_EROSION = "commitment_erosion"
    CAPABILITY_REVISION_DRIFT = "capability_revision_drift"
    SELF_BINDING_DRIFT = "self_binding_drift"
    CONTRADICTION_DRIVEN_FRACTURE = "contradiction_driven_fracture"
    UNRESOLVED_IDENTITY_TENSION = "unresolved_identity_tension"
    NO_CLEAN_DRIFT_CLAIM = "no_clean_drift_claim"


class N02BaselineValidityStatus(str, Enum):
    VALID = "valid"
    STALE = "stale"
    CONTESTED = "contested"
    MISSING = "missing"
    INVALIDATED = "invalidated"


class N02SubstrateChangeKind(str, Enum):
    LOCAL_REVISION = "local_revision"
    REPETITIVE_REVISION = "repetitive_revision"
    ABRUPT_INCOMPATIBLE_REPLACEMENT = "abrupt_incompatible_replacement"
    CONTEXT_SPLIT_SIGNAL = "context_split_signal"
    COMMITMENT_WEAKENING = "commitment_weakening"
    CAPABILITY_CONTOUR_SHIFT = "capability_contour_shift"
    TOOL_AVAILABILITY_UPDATE_ONLY = "tool_availability_update_only"
    SELF_BINDING_NOISY_FLUCTUATION = "self_binding_noisy_fluctuation"
    SELF_BINDING_CORE_SHIFT = "self_binding_core_shift"
    CONTRADICTION_ACCUMULATION = "contradiction_accumulation"
    TEXTUAL_REPHRASE_ONLY = "textual_rephrase_only"
    UNKNOWN = "unknown"


class N02ConflictStatus(str, Enum):
    NO_CONFLICT = "no_conflict"
    CONFLICT_PRESENT = "conflict_present"
    UNRESOLVED = "unresolved"


class N02ReflectionNeedLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class N02BaselineReference:
    baseline_id: str
    baseline_kind: N02IdentityRegionKind
    time_scope: str
    source_commitment_ids: tuple[str, ...]
    source_region_ids: tuple[str, ...]
    validity_status: N02BaselineValidityStatus
    confidence: float
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class N02CurrentIdentityEvidence:
    current_reference_id: str
    observed_region: N02IdentityRegionKind
    current_commitment_ids: tuple[str, ...]
    current_self_binding_refs: tuple[str, ...]
    capability_or_affordance_refs: tuple[str, ...]
    context_scope: str
    evidence_window: str
    confidence: float
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class N02IdentitySubstrateChange:
    change_id: str
    region: N02IdentityRegionKind
    change_kind: N02SubstrateChangeKind
    magnitude_hint: float
    affected_commitment_ids: tuple[str, ...]
    affected_capability_refs: tuple[str, ...]
    affected_self_binding_refs: tuple[str, ...]
    context_scope: str
    temporal_pattern: str
    confidence: float
    self_related: bool = True
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class N02CommitmentHistoryEvent:
    event_id: str
    commitment_id: str
    region: N02IdentityRegionKind
    event_kind: str
    previous_status: str
    current_status: str
    context_scope: str
    confidence: float
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class N02IdentityDriftEntry:
    drift_id: str
    affected_identity_region: N02IdentityRegionKind
    compared_time_scope: str
    baseline_reference_id: str | None
    current_reference_id: str
    drift_kind: N02DriftKind
    drift_magnitude: float
    continuity_preserved_flag: bool
    conflict_status: N02ConflictStatus
    reflection_need_level: N02ReflectionNeedLevel
    revision_pressure: str
    context_split_scope: str | None
    downstream_caution: tuple[str, ...]
    confidence: float
    affected_commitment_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class N02DriftLedger:
    ledger_id: str
    entries: tuple[N02IdentityDriftEntry, ...]
    baseline_refs: tuple[N02BaselineReference, ...]
    current_refs: tuple[N02CurrentIdentityEvidence, ...]
    substrate_changes: tuple[N02IdentitySubstrateChange, ...]
    no_claim_markers: tuple[str, ...]
    telemetry_summary: tuple[str, ...]
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class N02GateDecision:
    n02_consumer_ready: bool
    reflection_consumer_ready: bool
    consistency_consumer_ready: bool
    reflection_needed_count: int
    unresolved_identity_tension_count: int
    context_split_count: int
    no_clean_drift_count: int
    baseline_uncertain_count: int
    overreflection_guard_count: int
    text_diff_only_blocked_count: int
    substrate_ablation_or_missing_count: int
    downstream_caution_count: int
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class N02Telemetry:
    baseline_count: int
    current_reference_count: int
    substrate_change_count: int
    drift_entry_count: int
    stable_continuation_count: int
    bounded_revision_count: int
    reflection_needed_count: int
    unresolved_identity_tension_count: int
    context_split_count: int
    no_clean_drift_count: int
    baseline_uncertain_count: int
    overreflection_guard_count: int
    text_diff_only_blocked_count: int
    substrate_ablation_or_missing_count: int
    downstream_caution_count: int
    n02_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class N02ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    identity_drift_reflection_registry_only: bool
    no_metaphysical_identity_claim: bool
    no_autobiographical_relevance_claim: bool
    no_memory_lifecycle_claim: bool
    no_user_model_claim: bool
    no_commitment_rewrite_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class N02InputBundle:
    bundle_id: str
    baseline_references: tuple[N02BaselineReference, ...]
    current_references: tuple[N02CurrentIdentityEvidence, ...]
    substrate_changes: tuple[N02IdentitySubstrateChange, ...]
    commitment_history: tuple[N02CommitmentHistoryEvent, ...] = ()
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class N02Result:
    bundle_id: str
    drift_entries: tuple[N02IdentityDriftEntry, ...]
    ledger: N02DriftLedger
    telemetry: N02Telemetry
    gate: N02GateDecision
    scope_marker: N02ScopeMarker
    reason: str

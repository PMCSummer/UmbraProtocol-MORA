from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class S04CandidateClass(str, Enum):
    PRIVILEGED_INTEROCEPTIVE_REGULATORY = "privileged_interoceptive_regulatory"
    GENERIC_INTERNAL_BOOKKEEPING = "generic_internal_bookkeeping"
    MIXED_INTERNAL_EXTERNAL = "mixed_internal_external"
    TRANSIENT_CONTEXT_BOUND = "transient_context_bound"


class S04BindingStatus(str, Enum):
    STRONGLY_SELF_BOUND = "strongly_self_bound"
    WEAKLY_SELF_BOUND = "weakly_self_bound"
    PROVISIONALLY_BOUND = "provisionally_bound"
    CONTESTED_BINDING = "contested_binding"
    UNBOUND_INTERNAL = "unbound_internal"
    MIXED_INTERNAL_EXTERNAL_SIGNAL = "mixed_internal_external_signal"
    NO_STABLE_SELF_CORE_CLAIM = "no_stable_self_core_claim"


@dataclass(frozen=True, slots=True)
class S04CandidateSignal:
    channel_id: str
    candidate_class: S04CandidateClass
    regulatory_support_hint: float
    continuity_support_hint: float
    boundary_support_hint: float
    ownership_support_hint: float
    coupling_support_hint: float
    temporal_validity_hint: float
    contamination_hint: float
    source_authority: str
    provenance: str


@dataclass(frozen=True, slots=True)
class S04BindingEntry:
    binding_entry_id: str
    channel_or_group_id: str
    binding_status: S04BindingStatus
    binding_strength: float
    binding_basis: tuple[str, ...]
    coupling_support: float
    ownership_support: float
    boundary_support: float
    regulatory_support: float
    continuity_support: float
    temporal_persistence: int
    contamination_level: float
    current_validity: str
    provenance: str


@dataclass(frozen=True, slots=True)
class S04InteroceptiveSelfBindingState:
    binding_id: str
    tick_index: int
    entries: tuple[S04BindingEntry, ...]
    core_bound_channels: tuple[str, ...]
    peripheral_or_weakly_bound_channels: tuple[str, ...]
    contested_channels: tuple[str, ...]
    recently_unbound_channels: tuple[str, ...]
    no_stable_self_core_claim: bool
    strongest_binding_strength: float
    contamination_detected: bool
    rebinding_event: bool
    stale_binding_drop_count: int
    candidate_channels: tuple[str, ...]
    excluded_channels: tuple[str, ...]
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class S04SelfBindingGateDecision:
    core_consumer_ready: bool
    contested_consumer_ready: bool
    no_stable_core_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class S04ScopeMarker:
    scope: str
    rt01_contour_only: bool
    s04_first_slice_only: bool
    s05_implemented: bool
    full_self_model_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class S04Telemetry:
    binding_id: str
    tick_index: int
    strong_bound_count: int
    weak_bound_count: int
    provisional_count: int
    contested_count: int
    no_stable_core_claim: bool
    strongest_binding_strength: float
    contamination_detected: bool
    rebinding_event: bool
    stale_binding_drop_count: int
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class S04InteroceptiveSelfBindingResult:
    state: S04InteroceptiveSelfBindingState
    gate: S04SelfBindingGateDecision
    scope_marker: S04ScopeMarker
    telemetry: S04Telemetry
    reason: str

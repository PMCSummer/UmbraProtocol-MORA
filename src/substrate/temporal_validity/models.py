from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum


class TemporalCarryoverItemKind(str, Enum):
    STREAM_ANCHOR = "stream_anchor"
    CARRIED_ASSUMPTION = "carried_assumption"
    MODE_HOLD_PERMISSION = "mode_hold_permission"
    REVISIT_BASIS = "revisit_basis"
    BRANCH_ACCESS_GATE = "branch_access_gate"
    PROVISIONAL_BINDING_OR_PERMISSION = "provisional_binding_or_permission"


class TemporalValidityStatus(str, Enum):
    STILL_VALID = "still_valid"
    CONDITIONALLY_CARRIED = "conditionally_carried"
    NEEDS_PARTIAL_REVALIDATION = "needs_partial_revalidation"
    NEEDS_FULL_REVALIDATION = "needs_full_revalidation"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"
    DEPENDENCY_CONTAMINATED = "dependency_contaminated"
    NO_SAFE_REUSE_CLAIM = "no_safe_reuse_claim"


class RevalidationScope(str, Enum):
    NONE = "none"
    ITEM_LOCAL = "item_local"
    DEPENDENCY_LOCAL = "dependency_local"
    BOUNDED_GROUP = "bounded_group"
    STREAM_WIDE = "stream_wide"
    UNKNOWN = "unknown"


class TemporalValidityUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


class C05RestrictionCode(StrEnum):
    TEMPORAL_VALIDITY_STATE_MUST_BE_READ = "temporal_validity_state_must_be_read"
    ITEM_VALIDITY_STATUS_MUST_BE_READ = "item_validity_status_must_be_read"
    ITEM_DEPENDENCY_SET_MUST_BE_READ = "item_dependency_set_must_be_read"
    ITEM_REVALIDATION_SCOPE_MUST_BE_READ = "item_revalidation_scope_must_be_read"
    ITEM_INVALIDATION_TRIGGERS_MUST_BE_READ = "item_invalidation_triggers_must_be_read"
    SELECTIVE_REVALIDATION_TARGETS_MUST_BE_READ = (
        "selective_revalidation_targets_must_be_read"
    )
    PROVISIONAL_CARRY_MUST_BE_READ = "provisional_carry_must_be_read"
    DEPENDENCY_PROPAGATION_MUST_BE_READ = "dependency_propagation_must_be_read"
    NO_TTL_ONLY_SHORTCUT = "no_ttl_only_shortcut"
    NO_BLANKET_RESET_SHORTCUT = "no_blanket_reset_shortcut"
    NO_BLANKET_REUSE_SHORTCUT = "no_blanket_reuse_shortcut"
    NO_GLOBAL_RECOMPUTE_SHORTCUT = "no_global_recompute_shortcut"
    INSUFFICIENT_BASIS_FOR_REVALIDATION_PRESENT = (
        "insufficient_basis_for_revalidation_present"
    )
    PROVISIONAL_CARRY_ONLY_PRESENT = "provisional_carry_only_present"
    DEPENDENCY_GRAPH_INCOMPLETE_PRESENT = "dependency_graph_incomplete_present"
    INVALIDATION_POSSIBLE_BUT_UNPROVEN_PRESENT = (
        "invalidation_possible_but_unproven_present"
    )
    SELECTIVE_SCOPE_UNCERTAIN_PRESENT = "selective_scope_uncertain_present"
    NO_SAFE_REUSE_CLAIM_PRESENT = "no_safe_reuse_claim_present"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"


class TemporalValidityLedgerEventKind(str, Enum):
    ASSESSED = "assessed"
    STILL_VALID = "still_valid"
    CONDITIONALLY_CARRIED = "conditionally_carried"
    PARTIAL_REVALIDATION_REQUIRED = "partial_revalidation_required"
    FULL_REVALIDATION_REQUIRED = "full_revalidation_required"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"
    DEPENDENCY_CONTAMINATED = "dependency_contaminated"
    NO_SAFE_REUSE = "no_safe_reuse"


@dataclass(frozen=True, slots=True)
class TemporalCarryoverItem:
    item_id: str
    item_kind: TemporalCarryoverItemKind
    source_provenance: str
    dependency_set: tuple[str, ...]
    dependent_item_ids: tuple[str, ...]
    invalidation_triggers: tuple[str, ...]
    confidence: float
    basis: str


@dataclass(frozen=True, slots=True)
class TemporalValidityItem:
    item_id: str
    item_kind: TemporalCarryoverItemKind
    source_provenance: str
    dependency_set: tuple[str, ...]
    dependent_item_ids: tuple[str, ...]
    current_validity_status: TemporalValidityStatus
    reusable_now: bool
    revalidation_priority: float
    revalidation_scope: RevalidationScope
    invalidation_triggers: tuple[str, ...]
    last_validated_sequence_index: int
    grace_window_remaining: int
    provisional_horizon: int
    confidence: float
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class TemporalValidityLedgerEvent:
    event_id: str
    event_kind: TemporalValidityLedgerEventKind
    item_id: str
    stream_id: str
    reason: str
    reason_code: str
    provenance: str


@dataclass(frozen=True, slots=True)
class TemporalValidityState:
    validity_id: str
    stream_id: str
    source_stream_sequence_index: int
    items: tuple[TemporalValidityItem, ...]
    reusable_item_ids: tuple[str, ...]
    provisional_item_ids: tuple[str, ...]
    revalidation_item_ids: tuple[str, ...]
    invalidated_item_ids: tuple[str, ...]
    expired_item_ids: tuple[str, ...]
    dependency_contaminated_item_ids: tuple[str, ...]
    no_safe_reuse_item_ids: tuple[str, ...]
    selective_scope_targets: tuple[str, ...]
    insufficient_basis_for_revalidation: bool
    provisional_carry_only: bool
    dependency_graph_incomplete: bool
    invalidation_possible_but_unproven: bool
    selective_scope_uncertain: bool
    source_c01_state_ref: str
    source_c02_state_ref: str
    source_c03_state_ref: str
    source_c04_state_ref: str
    source_regulation_ref: str
    source_affordance_ref: str
    source_preference_ref: str
    source_viability_ref: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class TemporalValidityContext:
    prior_temporal_validity_state: TemporalValidityState | None = None
    source_lineage: tuple[str, ...] = ()
    step_delta: int = 1
    dependency_trigger_hits: tuple[str, ...] = ()
    context_shift_markers: tuple[str, ...] = ()
    contradicted_source_refs: tuple[str, ...] = ()
    withdrawn_source_refs: tuple[str, ...] = ()
    force_full_revalidation_items: tuple[str, ...] = ()
    allow_provisional_carry: bool = True
    dependency_graph_complete: bool = True
    default_grace_window: int = 2
    provisional_horizon_steps: int = 2
    expire_after_steps: int = 5
    disable_dependency_trigger_logic: bool = False
    disable_propagation_logic: bool = False
    disable_provisional_handling: bool = False
    disable_selective_scope_handling: bool = False
    expected_schema_version: str = "c05.temporal_validity.v1"


@dataclass(frozen=True, slots=True)
class TemporalValidityGateDecision:
    accepted: bool
    usability_class: TemporalValidityUsabilityClass
    restrictions: tuple[C05RestrictionCode, ...]
    reason: str
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class TemporalValidityTelemetry:
    source_lineage: tuple[str, ...]
    validity_id: str
    stream_id: str
    source_stream_sequence_index: int
    item_count: int
    reusable_count: int
    provisional_count: int
    revalidation_count: int
    invalidated_count: int
    expired_count: int
    dependency_contaminated_count: int
    no_safe_reuse_count: int
    selective_scope_target_count: int
    insufficient_basis_for_revalidation: bool
    provisional_carry_only: bool
    dependency_graph_incomplete: bool
    invalidation_possible_but_unproven: bool
    selective_scope_uncertain: bool
    ledger_events: tuple[TemporalValidityLedgerEvent, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: TemporalValidityGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class TemporalValidityResult:
    state: TemporalValidityState
    downstream_gate: TemporalValidityGateDecision
    telemetry: TemporalValidityTelemetry
    abstain: bool
    abstain_reason: str | None
    no_ttl_only_shortcut_dependency: bool
    no_blanket_reset_dependency: bool
    no_blanket_reuse_dependency: bool
    no_global_recompute_dependency: bool

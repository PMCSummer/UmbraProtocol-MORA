from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class O01EntityKind(str, Enum):
    CURRENT_USER_MODEL = "current_user_model"
    REFERENCED_OTHER_MODEL = "referenced_other_model"
    THIRD_PARTY_STUB = "third_party_stub"
    MINIMAL_OTHER_STUB = "minimal_other_stub"


class O01ModelScope(str, Enum):
    INTERACTION_LOCAL = "interaction_local"
    BOUNDED_RUNTIME = "bounded_runtime"


class O01UpdateEventKind(str, Enum):
    REINFORCE = "reinforce"
    REVISE = "revise"
    INVALIDATE = "invalidate"
    CONTRADICTION_PRESERVED = "contradiction_preserved"
    ENTITY_SPLIT_REQUIRED = "entity_split_required"
    NO_SAFE_STATE_CLAIM = "no_safe_state_claim"


class O01AttributionStatus(str, Enum):
    READY = "ready"
    PERSPECTIVE_UNDERCONSTRAINED = "perspective_underconstrained"
    ENTITY_NOT_INDIVIDUATED = "entity_not_individuated"
    NO_SAFE_STATE_CLAIM = "no_safe_state_claim"


@dataclass(frozen=True, slots=True)
class O01EntitySignal:
    signal_id: str
    entity_id_hint: str | None
    referent_label: str | None
    source_authority: str
    relation_class: str
    claim_value: str
    confidence: float
    grounded: bool
    quoted: bool
    turn_index: int
    provenance: str
    target_claim: str | None = None


@dataclass(frozen=True, slots=True)
class O01BeliefOverlay:
    belief_candidates: tuple[str, ...]
    ignorance_candidates: tuple[str, ...]
    belief_attribution_uncertainty: float
    evidence_basis: tuple[str, ...]
    revision_triggers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class O01EntityRevisionEvent:
    event_kind: O01UpdateEventKind
    field_name: str
    detail: str
    provenance: str


@dataclass(frozen=True, slots=True)
class O01EntityState:
    entity_id: str
    entity_kind: O01EntityKind
    model_scope: O01ModelScope
    identity_confidence: float
    stable_claims: tuple[str, ...]
    temporary_state_hypotheses: tuple[str, ...]
    probable_goals: tuple[str, ...]
    knowledge_boundary_estimates: tuple[str, ...]
    attention_targets: tuple[str, ...]
    trust_or_reliability_markers: tuple[str, ...]
    uncertainty_map: dict[str, float]
    interaction_history_links: tuple[str, ...]
    revision_history: tuple[O01EntityRevisionEvent, ...]
    belief_overlay: O01BeliefOverlay
    provenance: str


@dataclass(frozen=True, slots=True)
class O01OtherEntityModelState:
    model_id: str
    tick_index: int
    entities: tuple[O01EntityState, ...]
    current_user_entity_id: str | None
    referenced_other_entity_ids: tuple[str, ...]
    third_party_entity_ids: tuple[str, ...]
    minimal_other_entity_ids: tuple[str, ...]
    competing_entity_models: tuple[str, ...]
    entity_not_individuated: bool
    perspective_underconstrained: bool
    no_safe_state_claim: bool
    temporary_only_not_stable: bool
    knowledge_boundary_unknown: bool
    contradiction_count: int
    projection_guard_triggered: bool
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class O01OtherEntityModelGateDecision:
    current_user_model_ready: bool
    entity_individuation_ready: bool
    clarification_ready: bool
    downstream_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class O01ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    o01_first_slice_only: bool
    o02_o03_not_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class O01Telemetry:
    model_id: str
    tick_index: int
    entity_count: int
    current_user_model_ready: bool
    third_party_models_active: int
    stable_claim_count: int
    temporary_hypothesis_count: int
    contradiction_count: int
    knowledge_boundary_known_count: int
    projection_guard_triggered: bool
    no_safe_state_claim: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class O01OtherEntityModelResult:
    state: O01OtherEntityModelState
    gate: O01OtherEntityModelGateDecision
    scope_marker: O01ScopeMarker
    telemetry: O01Telemetry
    attribution_status: O01AttributionStatus
    reason: str

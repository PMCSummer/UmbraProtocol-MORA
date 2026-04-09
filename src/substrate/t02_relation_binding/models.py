from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class T02BindingStatus(str, Enum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    PROVISIONAL = "provisional"
    BLOCKED = "blocked"
    INCOMPATIBLE = "incompatible"
    CONFLICTED = "conflicted"
    RETRACTED = "retracted"


class T02ConstraintPolarity(str, Enum):
    REQUIRE = "require"
    FORBID = "forbid"
    PREFER = "prefer"


class T02PropagationStatus(str, Enum):
    ACTIVE = "active"
    STOPPED = "stopped"
    BLOCKED = "blocked"
    RETRACTED = "retracted"


class T02PropagationEffectType(str, Enum):
    NARROW_ROLE_CANDIDATES = "narrow_role_candidates"
    PRESERVE_CONFLICT = "preserve_conflict"
    RESTRICT_SCOPE = "restrict_scope"
    NO_EFFECT = "no_effect"


class T02ConstrainedSceneStatus(str, Enum):
    CONSTRAINED_SCENE_ASSEMBLED = "constrained_scene_assembled"
    LOCAL_CONSTRAINT_ONLY = "local_constraint_only"
    PROPAGATION_SCOPE_UNCERTAIN = "propagation_scope_uncertain"
    NO_CLEAN_BINDING_COMMIT = "no_clean_binding_commit"
    CONFLICT_PRESERVED = "conflict_preserved"
    AUTHORITY_INSUFFICIENT_FOR_PROPAGATION = "authority_insufficient_for_propagation"
    FRAGMENT_ONLY = "fragment_only"


class T02Operation(str, Enum):
    SELECT_BINDING = "select_binding"
    CONFIRM_BINDING = "confirm_binding"
    KEEP_PROVISIONAL = "keep_provisional"
    BLOCK_BINDING = "block_binding"
    MARK_INCOMPATIBLE = "mark_incompatible"
    PROPAGATE_CONSTRAINT = "propagate_constraint"
    STOP_PROPAGATION = "stop_propagation"
    PRESERVE_CONFLICT = "preserve_conflict"
    RETRACT_PROVISIONAL_BINDING = "retract_provisional_binding"
    NARROW_ROLE_CANDIDATES = "narrow_role_candidates"


class T02AssemblyMode(str, Enum):
    BOUNDED_CONSTRAINT_PROPAGATION = "bounded_constraint_propagation"
    GRAPH_EDGE_HEURISTIC_ABLATION = "graph_edge_heuristic_ablation"
    SPREADING_ACTIVATION_ABLATION = "spreading_activation_ablation"
    HIDDEN_LOGIC_ABLATION = "hidden_logic_ablation"
    NO_STOP_CONDITIONS_ABLATION = "no_stop_conditions_ablation"
    NO_CONFLICT_PRESERVATION_ABLATION = "no_conflict_preservation_ablation"


class ForbiddenT02Shortcut(str, Enum):
    GRAPH_EDGE_HEURISTIC_REBRANDING = "graph_edge_heuristic_rebranding"
    SPREADING_ACTIVATION_REBRANDING = "spreading_activation_rebranding"
    HIDDEN_LOGIC_SHORTCUT = "hidden_logic_shortcut"
    AUTHORITY_LEAK_PROPAGATION = "authority_leak_propagation"
    SCOPE_LEAK_PROPAGATION = "scope_leak_propagation"
    SILENT_CONFLICT_OVERWRITE = "silent_conflict_overwrite"


@dataclass(frozen=True, slots=True)
class T02RelationBinding:
    binding_id: str
    source_nodes: tuple[str, ...]
    relation_type: str
    role_constraints: tuple[str, ...]
    authority_basis: tuple[str, ...]
    confidence: float
    status: T02BindingStatus
    downstream_effects: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class T02ConstraintObject:
    constraint_id: str
    origin: str
    scope: str
    polarity: T02ConstraintPolarity
    authority_basis: tuple[str, ...]
    applicability_limits: tuple[str, ...]
    propagation_status: T02PropagationStatus
    provenance: str


@dataclass(frozen=True, slots=True)
class T02PropagationRecord:
    propagation_id: str
    trigger_binding_or_constraint: str
    affected_nodes_or_roles: tuple[str, ...]
    effect_type: T02PropagationEffectType
    scope: str
    stop_reason_or_none: str | None
    status: T02PropagationStatus
    provenance: str


@dataclass(frozen=True, slots=True)
class T02ConflictRecord:
    conflict_id: str
    conflicting_bindings_or_constraints: tuple[str, ...]
    conflict_class: str
    preserved_status: bool
    overwrite_forbidden: bool
    downstream_visibility: bool
    provenance: str


@dataclass(frozen=True, slots=True)
class T02ConstrainedSceneState:
    constrained_scene_id: str
    source_t01_scene_id: str
    source_t01_scene_status: str
    raw_scene_nodes: tuple[str, ...]
    raw_relation_candidates: tuple[tuple[str, str, str], ...]
    relation_bindings: tuple[T02RelationBinding, ...]
    constraint_objects: tuple[T02ConstraintObject, ...]
    propagation_records: tuple[T02PropagationRecord, ...]
    conflict_records: tuple[T02ConflictRecord, ...]
    narrowed_role_candidates: tuple[tuple[str, tuple[str, ...]], ...]
    scene_status: T02ConstrainedSceneStatus
    operations_applied: tuple[str, ...]
    source_authority_tags: tuple[str, ...]
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class T02GateDecision:
    pre_verbal_constraint_consumer_ready: bool
    no_clean_binding_commit: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class T02ScopeMarker:
    scope: str
    rt01_contour_only: bool
    t02_first_slice_only: bool
    t03_implemented: bool
    t04_implemented: bool
    o01_implemented: bool
    full_silent_thought_line_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class T02Telemetry:
    constrained_scene_id: str
    source_t01_scene_id: str
    scene_status: T02ConstrainedSceneStatus
    relation_bindings_count: int
    confirmed_bindings_count: int
    provisional_bindings_count: int
    blocked_bindings_count: int
    conflicted_bindings_count: int
    constraint_objects_count: int
    propagation_records_count: int
    stopped_propagation_count: int
    conflict_records_count: int
    pre_verbal_constraint_consumer_ready: bool
    no_clean_binding_commit: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class T02ConstrainedSceneResult:
    state: T02ConstrainedSceneState
    gate: T02GateDecision
    scope_marker: T02ScopeMarker
    telemetry: T02Telemetry
    reason: str

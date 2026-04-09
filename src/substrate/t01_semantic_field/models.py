from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class T01SceneStatus(str, Enum):
    SCENE_ASSEMBLED = "scene_assembled"
    SCENE_FRAGMENT_ONLY = "scene_fragment_only"
    COMPETING_SCENE_HYPOTHESES = "competing_scene_hypotheses"
    UNRESOLVED_RELATION_CLUSTER = "unresolved_relation_cluster"
    AUTHORITY_INSUFFICIENT_FOR_BINDING = "authority_insufficient_for_binding"
    NO_CLEAN_SCENE_COMMIT = "no_clean_scene_commit"
    PROVISIONAL_SCENE_ONLY = "provisional_scene_only"


class T01StabilityState(str, Enum):
    STABLE = "stable"
    PROVISIONAL = "provisional"
    CONTESTED = "contested"
    FRAGMENTARY = "fragmentary"
    DEGRADED = "degraded"


class T01FieldOperation(str, Enum):
    ASSEMBLE = "assemble"
    UPDATE = "update"
    DECAY = "decay"
    RECENTER = "recenter"
    SPLIT = "split"
    MERGE = "merge"
    SLOT_FILL = "slot_fill"
    RELATION_REWEIGHT = "relation_reweight"


class T01AssemblyMode(str, Enum):
    SEMANTIC_FIELD = "semantic_field"
    FLAT_TAG_ABLATION = "flat_tag_ablation"
    TOKEN_GRAPH_ABLATION = "token_graph_ablation"
    HIDDEN_TEXT_ABLATION = "hidden_text_ablation"


class ForbiddenT01Shortcut(str, Enum):
    HIDDEN_TEXT_BUFFER_SURROGATE = "hidden_text_buffer_surrogate"
    BAG_OF_TAGS_REBRANDING = "bag_of_tags_rebranding"
    TOKEN_GRAPH_REBRANDING = "token_graph_rebranding"
    PREMATURE_SCENE_CLOSURE = "premature_scene_closure"
    MEMORY_POLLUTION_REFRAMED_AS_SCENE_FACT = "memory_pollution_reframed_as_scene_fact"
    IMMEDIATE_VERBALIZATION_SHORTCUT = "immediate_verbalization_shortcut"


@dataclass(frozen=True, slots=True)
class T01Entity:
    entity_id: str
    label: str
    entity_type: str
    provisional: bool
    source_authority_tag: str


@dataclass(frozen=True, slots=True)
class T01RelationEdge:
    edge_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    weight: float
    provisional: bool
    contested: bool
    source_authority_tag: str


@dataclass(frozen=True, slots=True)
class T01RoleBinding:
    role_id: str
    entity_id: str | None
    binding_confidence: float
    provisional: bool
    unresolved: bool
    source_authority_tag: str


@dataclass(frozen=True, slots=True)
class T01UnresolvedSlot:
    slot_id: str
    slot_kind: str
    candidate_entity_ids: tuple[str, ...]
    contested: bool
    reason: str


@dataclass(frozen=True, slots=True)
class T01TemporalLink:
    link_id: str
    source_entity_id: str
    target_entity_id: str
    temporal_relation: str
    provisional: bool


@dataclass(frozen=True, slots=True)
class T01ExpectationLink:
    link_id: str
    source_entity_id: str
    target_entity_id: str
    predicate: str
    confidence: float
    provisional: bool


@dataclass(frozen=True, slots=True)
class T01ActiveSemanticFieldState:
    scene_id: str
    scene_status: T01SceneStatus
    active_entities: tuple[T01Entity, ...]
    relation_edges: tuple[T01RelationEdge, ...]
    role_bindings: tuple[T01RoleBinding, ...]
    active_predicates: tuple[str, ...]
    unresolved_slots: tuple[T01UnresolvedSlot, ...]
    attention_weights: tuple[tuple[str, float], ...]
    salience_weights: tuple[tuple[str, float], ...]
    temporal_links: tuple[T01TemporalLink, ...]
    expectation_links: tuple[T01ExpectationLink, ...]
    source_authority_tags: tuple[str, ...]
    stability_state: T01StabilityState
    operations_applied: tuple[str, ...]
    wording_surface_ref: str | None
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class T01FieldGateDecision:
    pre_verbal_consumer_ready: bool
    no_clean_scene_commit: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class T01ScopeMarker:
    scope: str
    rt01_contour_only: bool
    t01_first_slice_only: bool
    t02_implemented: bool
    t03_implemented: bool
    t04_implemented: bool
    o01_implemented: bool
    full_silent_thought_line_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class T01Telemetry:
    scene_id: str
    scene_status: T01SceneStatus
    stability_state: T01StabilityState
    active_entities_count: int
    relation_edges_count: int
    unresolved_slots_count: int
    contested_relations_count: int
    pre_verbal_consumer_ready: bool
    no_clean_scene_commit: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class T01ActiveFieldResult:
    state: T01ActiveSemanticFieldState
    gate: T01FieldGateDecision
    scope_marker: T01ScopeMarker
    telemetry: T01Telemetry
    reason: str

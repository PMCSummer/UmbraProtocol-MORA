from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SemanticUnitKind(str, Enum):
    FRAME_NODE = "frame_node"
    ROLE_SLOT_NODE = "role_slot_node"
    OPERATOR_NODE = "operator_node"
    SOURCE_NODE = "source_node"
    MODUS_NODE = "modus_node"


class DictumOrModusClass(str, Enum):
    DICTUM = "dictum"
    MODUS = "modus"


class PolarityClass(str, Enum):
    AFFIRMATIVE = "affirmative"
    NEGATED = "negated"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class CertaintyClass(str, Enum):
    ASSERTED = "asserted"
    HYPOTHETICAL = "hypothetical"
    INTERROGATIVE = "interrogative"
    QUOTED = "quoted"
    REPORTED = "reported"
    UNCERTAIN = "uncertain"


class GraphUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class SemanticUnit:
    semantic_unit_id: str
    unit_kind: SemanticUnitKind
    predicate: str | None
    role_bindings: tuple[str, ...]
    modifier_links: tuple[str, ...]
    source_scope: tuple[str, ...]
    dictum_or_modus_class: DictumOrModusClass
    polarity: PolarityClass
    certainty_class: CertaintyClass
    provenance: str
    confidence: float


@dataclass(frozen=True, slots=True)
class RoleBinding:
    binding_id: str
    frame_node_id: str
    role_label: str
    target_ref: str | None
    unresolved: bool
    unresolved_reason: str | None
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class GraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_kind: str
    uncertain: bool
    reason: str | None
    confidence: float


@dataclass(frozen=True, slots=True)
class PropositionCandidate:
    proposition_id: str
    frame_node_id: str
    role_binding_ids: tuple[str, ...]
    source_scope_refs: tuple[str, ...]
    dictum_or_modus_class: DictumOrModusClass
    polarity: PolarityClass
    certainty_class: CertaintyClass
    unresolved: bool
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class GraphAlternative:
    alternative_id: str
    competing_ref_ids: tuple[str, ...]
    reason: str
    confidence: float


@dataclass(frozen=True, slots=True)
class RuntimeGraphBundle:
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_scaffold_ids: tuple[str, ...]
    linked_dictum_ids: tuple[str, ...]
    semantic_units: tuple[SemanticUnit, ...]
    role_bindings: tuple[RoleBinding, ...]
    graph_edges: tuple[GraphEdge, ...]
    proposition_candidates: tuple[PropositionCandidate, ...]
    graph_alternatives: tuple[GraphAlternative, ...]
    unresolved_role_slots: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    no_final_semantic_closure: bool
    reason: str


@dataclass(frozen=True, slots=True)
class RuntimeGraphGateDecision:
    accepted: bool
    usability_class: GraphUsabilityClass
    restrictions: tuple[str, ...]
    reason: str
    accepted_proposition_ids: tuple[str, ...]
    rejected_proposition_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeGraphTelemetry:
    source_lineage: tuple[str, ...]
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    semantic_unit_count: int
    role_binding_count: int
    edge_count: int
    proposition_count: int
    alternative_count: int
    unresolved_role_slot_count: int
    polarity_classes: tuple[str, ...]
    certainty_classes: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: RuntimeGraphGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class RuntimeGraphResult:
    bundle: RuntimeGraphBundle
    telemetry: RuntimeGraphTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_semantic_closure: bool

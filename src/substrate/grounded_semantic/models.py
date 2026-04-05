from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class GroundedUnitKind(str, Enum):
    PREDICATE = "predicate"
    ARGUMENT = "argument"
    OPERATOR = "operator"
    SOURCE_MARKER = "source_marker"
    DEIXIS_PLACEHOLDER = "deixis_placeholder"
    PHRASE_BOUNDARY = "phrase_boundary"
    CLAUSE_BOUNDARY = "clause_boundary"
    CARRIER = "carrier"
    UNKNOWN = "unknown"


class ChannelOrigin(str, Enum):
    L04_DICTUM = "l04_dictum"
    L01_SURFACE = "l01_surface"
    L02_SYNTAX = "l02_syntax"
    L03_LEXICAL = "l03_lexical"
    M03_MEMORY = "m03_memory"
    O03_COOPERATION = "o03_cooperation"
    DERIVED = "derived"


class AmbiguityState(str, Enum):
    STABLE = "stable"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"
    PROVISIONAL = "provisional"
    UNKNOWN = "unknown"


class OperatorKind(str, Enum):
    NEGATION = "negation"
    QUOTATION = "quotation"
    INTERROGATION = "interrogation"
    MODALITY = "modality"
    COORDINATION = "coordination"
    CONDITIONAL = "conditional"
    DISCOURSE_PARTICLE = "discourse_particle"


class CarrierKind(str, Enum):
    DICTUM_CONTENT = "dictum_content"
    MODUS_STANCE = "modus_stance"


class SourceAnchorKind(str, Enum):
    QUOTE_BOUNDARY = "quote_boundary"
    REPORTED_SPEECH = "reported_speech"
    SPEAKER_MARKER = "speaker_marker"
    DEIXIS_PLACEHOLDER = "deixis_placeholder"
    UNKNOWN = "unknown"


class UncertaintyKind(str, Enum):
    TOKENIZATION_AMBIGUOUS = "tokenization_ambiguous"
    ATTACHMENT_AMBIGUOUS = "attachment_ambiguous"
    CLAUSE_BOUNDARY_UNCERTAIN = "clause_boundary_uncertain"
    OPERATOR_SCOPE_UNCERTAIN = "operator_scope_uncertain"
    SOURCE_SCOPE_UNCERTAIN = "source_scope_uncertain"
    REFERENT_UNRESOLVED = "referent_unresolved"
    SURFACE_CORRUPTION_PRESENT = "surface_corruption_present"


@dataclass(frozen=True, slots=True)
class SpanRange:
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class GroundedSubstrateUnit:
    unit_id: str
    span_start: int
    span_end: int
    raw_surface: str
    normalized_form: str
    unit_kind: GroundedUnitKind
    channel_origin: ChannelOrigin
    confidence: float
    provenance: str
    ambiguity_state: AmbiguityState


@dataclass(frozen=True, slots=True)
class OperatorAttachment:
    operator_id: str
    target_ref: str
    relation: str
    unresolved: bool
    reason: str


@dataclass(frozen=True, slots=True)
class PhraseScaffold:
    scaffold_id: str
    clause_boundaries: tuple[SpanRange, ...]
    phrase_boundaries: tuple[SpanRange, ...]
    operator_attachments: tuple[OperatorAttachment, ...]
    local_scope_relations: tuple[str, ...]
    candidate_head_links: tuple[tuple[str, str], ...]
    unresolved_attachments: tuple[str, ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class OperatorCarrier:
    operator_id: str
    operator_kind: OperatorKind
    carrier_unit_ids: tuple[str, ...]
    scope_anchor_refs: tuple[str, ...]
    scope_uncertain: bool
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class DictumCarrier:
    carrier_id: str
    dictum_candidate_id: str
    predicate_ref: str
    argument_slot_refs: tuple[str, ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class ModusCarrier:
    carrier_id: str
    dictum_candidate_id: str
    stance_kind: str
    evidence_refs: tuple[str, ...]
    unresolved: bool
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class SourceAnchor:
    anchor_id: str
    anchor_kind: SourceAnchorKind
    span_start: int
    span_end: int
    marker_text: str
    unresolved: bool
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class UncertaintyMarker:
    marker_id: str
    uncertainty_kind: UncertaintyKind
    related_refs: tuple[str, ...]
    reason: str
    confidence: float


@dataclass(frozen=True, slots=True)
class GroundedSemanticBundle:
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    source_modus_ref: str | None
    source_modus_ref_kind: str
    source_modus_lineage_ref: str | None
    source_discourse_update_ref: str | None
    source_discourse_update_ref_kind: str
    source_discourse_update_lineage_ref: str | None
    linked_dictum_candidate_ids: tuple[str, ...]
    linked_modus_record_ids: tuple[str, ...]
    linked_update_proposal_ids: tuple[str, ...]
    substrate_units: tuple[GroundedSubstrateUnit, ...]
    phrase_scaffolds: tuple[PhraseScaffold, ...]
    operator_carriers: tuple[OperatorCarrier, ...]
    dictum_carriers: tuple[DictumCarrier, ...]
    modus_carriers: tuple[ModusCarrier, ...]
    source_anchors: tuple[SourceAnchor, ...]
    uncertainty_markers: tuple[UncertaintyMarker, ...]
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    normative_l05_l06_route_active: bool
    legacy_surface_cue_fallback_used: bool
    legacy_surface_cue_path_not_normative: bool
    l04_only_input_not_equivalent_to_l05_l06_route: bool
    discourse_update_not_inferred_from_surface_when_l06_available: bool
    l06_blocked_update_present: bool
    l06_guarded_continue_present: bool
    no_final_semantic_resolution: bool
    reason: str


@dataclass(frozen=True, slots=True)
class GroundedSemanticGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_scaffold_ids: tuple[str, ...]
    rejected_scaffold_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class GroundedSemanticTelemetry:
    source_lineage: tuple[str, ...]
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    source_modus_ref: str | None
    source_modus_ref_kind: str
    source_modus_lineage_ref: str | None
    source_discourse_update_ref: str | None
    source_discourse_update_ref_kind: str
    source_discourse_update_lineage_ref: str | None
    substrate_unit_count: int
    phrase_scaffold_count: int
    operator_carrier_count: int
    dictum_carrier_count: int
    modus_carrier_count: int
    source_anchor_count: int
    uncertainty_marker_count: int
    operator_kinds: tuple[str, ...]
    uncertainty_kinds: tuple[str, ...]
    reversible_span_mapping_present: bool
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    normative_l05_l06_route_active: bool
    legacy_surface_cue_fallback_used: bool
    l06_blocked_update_present: bool
    l06_guarded_continue_present: bool
    attempted_paths: tuple[str, ...]
    downstream_gate: GroundedSemanticGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class GroundedSemanticResult:
    bundle: GroundedSemanticBundle
    telemetry: GroundedSemanticTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_semantic_resolution: bool

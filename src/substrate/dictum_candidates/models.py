from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.language_surface.models import RawSpan


class DictumPolarity(str, Enum):
    AFFIRMATIVE = "affirmative"
    NEGATED = "negated"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class TemporalAnchorKind(str, Enum):
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"
    CONTEXTUAL = "contextual"
    UNSPECIFIED = "unspecified"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class PredicateFrame:
    frame_id: str
    predicate_token_id: str
    predicate_span: RawSpan
    predicate_lexeme_candidate_ids: tuple[str, ...]
    clause_id: str
    quotation_sensitive: bool
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class ArgumentSlot:
    slot_id: str
    role_label: str
    token_id: str
    token_span: RawSpan
    lexical_candidate_ids: tuple[str, ...]
    reference_candidate_ids: tuple[str, ...]
    unresolved: bool
    unresolved_reason: str | None
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class ScopeMarker:
    scope_marker_id: str
    marker_kind: str
    affected_slot_ids: tuple[str, ...]
    ambiguous: bool
    reason: str
    confidence: float


@dataclass(frozen=True, slots=True)
class NegationMarker:
    negation_marker_id: str
    carrier_token_ids: tuple[str, ...]
    scope_target_slot_ids: tuple[str, ...]
    scope_ambiguous: bool
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class TemporalMarker:
    temporal_marker_id: str
    anchor_kind: TemporalAnchorKind
    token_ids: tuple[str, ...]
    unresolved: bool
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class MagnitudeMarker:
    magnitude_marker_id: str
    marker_kind: str
    token_ids: tuple[str, ...]
    value_hint: str | None
    unresolved: bool
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class UnderspecifiedSlot:
    underspecified_id: str
    slot_id_or_field: str
    reason: str
    source_ref_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class DictumAmbiguity:
    ambiguity_id: str
    dictum_candidate_id: str
    reason: str
    related_slot_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class DictumConflict:
    conflict_id: str
    dictum_candidate_ids: tuple[str, ...]
    reason: str
    confidence: float


@dataclass(frozen=True, slots=True)
class DictumUnknown:
    unknown_id: str
    dictum_candidate_ref: str | None
    reason: str
    source_ref_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class DictumCandidate:
    dictum_candidate_id: str
    source_syntax_hypothesis_ref: str
    source_lexical_grounding_ref: str
    source_surface_ref: str | None
    predicate_frame: PredicateFrame
    argument_slots: tuple[ArgumentSlot, ...]
    scope_markers: tuple[ScopeMarker, ...]
    negation_markers: tuple[NegationMarker, ...]
    temporal_markers: tuple[TemporalMarker, ...]
    magnitude_markers: tuple[MagnitudeMarker, ...]
    polarity: DictumPolarity
    underspecified_slots: tuple[UnderspecifiedSlot, ...]
    ambiguity_reasons: tuple[str, ...]
    quotation_sensitive: bool
    confidence: float
    provenance: str
    no_final_resolution_performed: bool


@dataclass(frozen=True, slots=True)
class DictumCandidateBundle:
    source_lexical_grounding_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_syntax_hypothesis_ids: tuple[str, ...]
    linked_lexical_candidate_ids: tuple[str, ...]
    dictum_candidates: tuple[DictumCandidate, ...]
    ambiguities: tuple[DictumAmbiguity, ...]
    conflicts: tuple[DictumConflict, ...]
    unknowns: tuple[DictumUnknown, ...]
    blocked_candidate_reasons: tuple[str, ...]
    no_final_resolution_performed: bool
    reason: str
    input_lexical_basis_classes: tuple[str, ...] = ()
    fallback_basis_present: bool = False
    lexicon_basis_missing_or_capped: bool = False
    no_strong_lexical_basis_from_upstream: bool = False
    lexicon_handoff_missing_upstream: bool = False


@dataclass(frozen=True, slots=True)
class DictumGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_candidate_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class DictumTelemetry:
    source_lineage: tuple[str, ...]
    input_syntax_refs: tuple[str, ...]
    input_lexical_grounding_ref: str
    input_surface_ref: str | None
    processed_candidate_ids: tuple[str, ...]
    dictum_candidate_count: int
    underspecified_slot_count: int
    negation_marker_count: int
    temporal_marker_count: int
    magnitude_marker_count: int
    scope_ambiguity_count: int
    conflict_count: int
    blocked_candidate_count: int
    ambiguity_reasons: tuple[str, ...]
    attempted_construction_paths: tuple[str, ...]
    input_lexical_basis_classes: tuple[str, ...]
    fallback_basis_present: bool
    lexicon_basis_missing_or_capped: bool
    no_strong_lexical_basis_from_upstream: bool
    lexicon_handoff_missing_upstream: bool
    downstream_gate: DictumGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class DictumCandidateResult:
    bundle: DictumCandidateBundle
    telemetry: DictumTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_resolution_performed: bool

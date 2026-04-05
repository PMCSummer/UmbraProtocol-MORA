from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.language_surface.models import RawSpan


class LexicalCandidateType(str, Enum):
    SENSE = "sense"
    ENTITY = "entity"
    REFERENCE = "reference"
    DEIXIS = "deixis"


class ReferenceKind(str, Enum):
    PRONOUN = "pronoun"
    INDEXICAL = "indexical"
    DISCOURSE_LINK = "discourse_link"
    ELLIPSIS = "ellipsis"
    UNKNOWN = "unknown"


class DeixisKind(str, Enum):
    SPEAKER = "speaker"
    ADDRESSEE = "addressee"
    LOCATION = "location"
    TIME = "time"
    OBJECT = "object"
    UNKNOWN = "unknown"


class LexicalBasisClass(str, Enum):
    LEXICON_BACKED = "lexicon_backed"
    LEXICON_CAPPED_UNKNOWN = "lexicon_capped_unknown"
    HEURISTIC_FALLBACK = "heuristic_fallback"
    NO_USABLE_LEXICAL_BASIS = "no_usable_lexical_basis"


class LexicalEvidenceKind(str, Enum):
    MENTION_ANCHOR = "mention_anchor"
    BASIS_CLASS = "basis_class"
    SENSE_CUE = "sense_cue"
    ENTITY_CUE = "entity_cue"
    REFERENCE_CUE = "reference_cue"
    DEIXIS_CUE = "deixis_cue"


@dataclass(frozen=True, slots=True)
class MentionAnchor:
    mention_id: str
    token_id: str
    raw_span: RawSpan
    surface_text: str
    normalized_text: str
    syntax_hypothesis_ref: str
    supporting_syntax_hypothesis_refs: tuple[str, ...]
    inside_quote: bool
    confidence: float


@dataclass(frozen=True, slots=True)
class MentionLexicalBasis:
    mention_id: str
    token_id: str
    basis_class: LexicalBasisClass
    lexicon_used: bool
    lexicon_usable: bool
    lexicon_unknown_classes: tuple[str, ...]
    lexicon_matched_entry_ids: tuple[str, ...]
    lexicon_matched_sense_ids: tuple[str, ...]
    lexicon_context_blocked_entry_ids: tuple[str, ...]
    heuristic_fallback_used: bool
    heuristic_fallback_reason: str | None
    no_strong_lexical_claim_from_fallback: bool


@dataclass(frozen=True, slots=True)
class LexicalEvidenceRecord:
    evidence_id: str
    mention_id: str | None
    token_id: str | None
    evidence_kind: LexicalEvidenceKind
    source_ref_ids: tuple[str, ...]
    supports_dimensions: tuple[str, ...]
    unresolved: bool
    reason: str


@dataclass(frozen=True, slots=True)
class LexemeCandidate:
    candidate_id: str
    mention_id: str
    token_id: str
    candidate_type: LexicalCandidateType
    label: str
    confidence: float
    entropy: float
    evidence: str
    discourse_context_ref: str | None = None


@dataclass(frozen=True, slots=True)
class SenseCandidate:
    candidate_id: str
    mention_id: str
    token_id: str
    sense_key: str
    confidence: float
    entropy: float
    evidence: str


@dataclass(frozen=True, slots=True)
class EntityCandidate:
    candidate_id: str
    mention_id: str
    token_id: str
    entity_ref: str
    entity_type: str
    confidence: float
    evidence: str
    discourse_context_ref: str | None = None


@dataclass(frozen=True, slots=True)
class DeixisCandidate:
    candidate_id: str
    mention_id: str
    token_id: str
    deixis_kind: DeixisKind
    target_ref: str | None
    confidence: float
    unresolved: bool
    evidence: str
    discourse_context_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ReferenceHypothesis:
    reference_id: str
    mention_id: str
    token_id: str
    reference_kind: ReferenceKind
    candidate_ref_ids: tuple[str, ...]
    confidence: float
    unresolved: bool
    evidence: str
    discourse_context_ref: str | None = None


@dataclass(frozen=True, slots=True)
class GroundingConflict:
    conflict_id: str
    mention_id: str
    candidate_ids: tuple[str, ...]
    reason: str
    confidence: float


@dataclass(frozen=True, slots=True)
class GroundingUnknownState:
    unknown_id: str
    mention_id: str
    token_id: str
    reason: str
    confidence: float


@dataclass(frozen=True, slots=True)
class LexicalDiscourseContext:
    context_ref: str = "discourse:default"
    entity_bindings: tuple[tuple[str, str], ...] = ()
    indexical_bindings: tuple[tuple[str, str], ...] = ()
    recent_mentions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LexicalGroundingBundle:
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_hypothesis_ids: tuple[str, ...]
    mention_anchors: tuple[MentionAnchor, ...]
    lexical_basis_records: tuple[MentionLexicalBasis, ...]
    lexeme_candidates: tuple[LexemeCandidate, ...]
    sense_candidates: tuple[SenseCandidate, ...]
    entity_candidates: tuple[EntityCandidate, ...]
    reference_hypotheses: tuple[ReferenceHypothesis, ...]
    deixis_candidates: tuple[DeixisCandidate, ...]
    unknown_states: tuple[GroundingUnknownState, ...]
    conflicts: tuple[GroundingConflict, ...]
    ambiguity_reasons: tuple[str, ...]
    syntax_instability_present: bool
    lexicon_primary_used: bool
    heuristic_fallback_used: bool
    no_strong_lexical_claim_from_fallback: bool
    fallback_reasons: tuple[str, ...]
    no_final_resolution_performed: bool
    reason: str
    lexicon_handoff_present: bool = False
    lexicon_query_attempted: bool = False
    lexicon_usable_basis_present: bool = False
    lexicon_backed_mentions_count: int = 0
    lexicon_handoff_missing: bool = False
    lexical_basis_degraded: bool = False
    no_strong_lexical_claim_without_lexicon: bool = False
    evidence_records: tuple[LexicalEvidenceRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class LexicalGroundingGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_candidate_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class LexicalGroundingTelemetry:
    source_lineage: tuple[str, ...]
    input_syntax_ref: str
    input_surface_ref: str | None
    processed_mention_ids: tuple[str, ...]
    generated_candidate_ids: tuple[str, ...]
    candidate_count: int
    reference_candidate_count: int
    entity_candidate_count: int
    sense_candidate_count: int
    unknown_count: int
    conflict_count: int
    syntax_hypothesis_count: int
    syntax_instability_mention_count: int
    lexicon_primary_used: bool
    lexicon_handoff_present: bool
    lexicon_query_attempted: bool
    lexicon_usable_basis_present: bool
    lexicon_backed_mentions_count: int
    lexicon_backed_mention_count: int
    lexicon_capped_unknown_mention_count: int
    heuristic_fallback_mention_count: int
    no_usable_lexical_basis_mention_count: int
    fallback_reasons: tuple[str, ...]
    no_strong_lexical_claim_from_fallback: bool
    ambiguity_reasons: tuple[str, ...]
    discourse_context_keys_used: tuple[str, ...]
    attempted_grounding_paths: tuple[str, ...]
    blocked_grounding_reasons: tuple[str, ...]
    downstream_gate: LexicalGroundingGateDecision
    causal_basis: str
    lexicon_handoff_missing: bool = False
    lexical_basis_degraded: bool = False
    no_strong_lexical_claim_without_lexicon: bool = False
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class LexicalGroundingResult:
    bundle: LexicalGroundingBundle
    telemetry: LexicalGroundingTelemetry
    confidence: float
    lexicon_primary_used: bool
    lexicon_handoff_present: bool
    lexicon_query_attempted: bool
    lexicon_usable_basis_present: bool
    lexicon_backed_mentions_count: int
    heuristic_fallback_used: bool
    no_usable_lexical_basis: bool
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_resolution_performed: bool
    lexicon_handoff_missing: bool = False
    lexical_basis_degraded: bool = False
    no_strong_lexical_claim_without_lexicon: bool = False

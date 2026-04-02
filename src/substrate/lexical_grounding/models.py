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


@dataclass(frozen=True, slots=True)
class MentionAnchor:
    mention_id: str
    token_id: str
    raw_span: RawSpan
    surface_text: str
    normalized_text: str
    syntax_hypothesis_ref: str
    confidence: float


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
    lexeme_candidates: tuple[LexemeCandidate, ...]
    sense_candidates: tuple[SenseCandidate, ...]
    entity_candidates: tuple[EntityCandidate, ...]
    reference_hypotheses: tuple[ReferenceHypothesis, ...]
    deixis_candidates: tuple[DeixisCandidate, ...]
    unknown_states: tuple[GroundingUnknownState, ...]
    conflicts: tuple[GroundingConflict, ...]
    ambiguity_reasons: tuple[str, ...]
    no_final_resolution_performed: bool
    reason: str


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
    ambiguity_reasons: tuple[str, ...]
    discourse_context_keys_used: tuple[str, ...]
    attempted_grounding_paths: tuple[str, ...]
    blocked_grounding_reasons: tuple[str, ...]
    downstream_gate: LexicalGroundingGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class LexicalGroundingResult:
    bundle: LexicalGroundingBundle
    telemetry: LexicalGroundingTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_resolution_performed: bool

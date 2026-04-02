from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.language_surface.models import RawSpan


class MorphPos(str, Enum):
    WORD = "word"
    VERB_LIKE = "verb_like"
    PRONOUN = "pronoun"
    CONJUNCTION = "conjunction"
    NEGATION_PARTICLE = "negation_particle"
    PUNCTUATION = "punctuation"
    QUOTE = "quote"
    CODE = "code"
    UNKNOWN = "unknown"


class MorphNumber(str, Enum):
    SINGULAR = "singular"
    PLURAL = "plural"
    UNKNOWN = "unknown"


class AgreementStatus(str, Enum):
    MATCH = "match"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"


class ClauseBoundaryKind(str, Enum):
    SENTENCE = "sentence"
    CLAUSE = "clause"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MorphTokenFeatures:
    token_id: str
    raw_span: RawSpan
    coarse_pos: MorphPos
    number: MorphNumber
    feature_map: tuple[tuple[str, str], ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class MorphAgreementCue:
    cue_id: str
    controller_token_id: str
    target_token_id: str
    feature_name: str
    status: AgreementStatus
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class SyntaxEdge:
    edge_id: str
    head_token_id: str
    dependent_token_id: str
    relation: str
    clause_id: str
    confidence: float


@dataclass(frozen=True, slots=True)
class UnresolvedAttachment:
    unresolved_id: str
    dependent_token_id: str
    candidate_head_ids: tuple[str, ...]
    relation_hint: str
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class ClauseNode:
    clause_id: str
    raw_span: RawSpan
    token_ids: tuple[str, ...]
    boundary_kind: ClauseBoundaryKind
    negation_carrier_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class ClauseGraph:
    clauses: tuple[ClauseNode, ...]
    inter_clause_edges: tuple[tuple[str, str, str], ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class SyntaxHypothesis:
    hypothesis_id: str
    clause_graph: ClauseGraph
    edges: tuple[SyntaxEdge, ...]
    unresolved_attachments: tuple[UnresolvedAttachment, ...]
    token_features: tuple[MorphTokenFeatures, ...]
    agreement_cues: tuple[MorphAgreementCue, ...]
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class SyntaxHypothesisSet:
    source_surface_ref: str
    hypotheses: tuple[SyntaxHypothesis, ...]
    ambiguity_present: bool
    no_selected_winner: bool
    reason: str


@dataclass(frozen=True, slots=True)
class SyntaxDownstreamGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_hypothesis_ids: tuple[str, ...]
    rejected_hypothesis_ids: tuple[str, ...]
    hypothesis_set_ref: str | None = None


@dataclass(frozen=True, slots=True)
class SyntaxTelemetry:
    source_lineage: tuple[str, ...]
    input_surface_ref: str
    input_segment_spans: tuple[tuple[int, int], ...]
    hypothesis_count: int
    unresolved_edge_count: int
    clause_count: int
    agreement_cue_count: int
    morphology_feature_count: int
    negation_carrier_count: int
    ambiguity_reasons: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: SyntaxDownstreamGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class SyntaxHypothesisResult:
    hypothesis_set: SyntaxHypothesisSet
    telemetry: SyntaxTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None

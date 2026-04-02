from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class TokenKind(str, Enum):
    WORD = "word"
    PUNCTUATION = "punctuation"
    QUOTE_MARK = "quote_mark"
    ELLIPSIS = "ellipsis"
    CODE_LITERAL = "code_literal"
    REPAIR_FRAGMENT = "repair_fragment"
    UNKNOWN = "unknown"


class SegmentKind(str, Enum):
    SENTENCE = "sentence"
    CLAUSE = "clause"
    UNKNOWN = "unknown"


class QuoteKind(str, Enum):
    DOUBLE = "double_quote"
    SINGLE = "single_quote"
    ANGLED = "angled_quote"
    UNKNOWN = "unknown_quote"


class InsertionKind(str, Enum):
    PARENTHETICAL = "parenthetical"
    CODE = "code"
    REPAIR_FRAGMENT = "repair_fragment"
    OTHER = "other"


class AmbiguityKind(str, Enum):
    BOUNDARY_UNCERTAIN_ELLIPSIS = "boundary_uncertain_ellipsis"
    BOUNDARY_UNCERTAIN_PUNCT_CLUSTER = "boundary_uncertain_punct_cluster"
    QUOTE_BOUNDARY_UNCERTAIN = "quote_boundary_uncertain"
    TERMINAL_BOUNDARY_MISSING = "terminal_boundary_missing"
    NOISY_SEPARATOR = "noisy_separator"


@dataclass(frozen=True, slots=True)
class RawSpan:
    start: int
    end: int
    raw_text: str


@dataclass(frozen=True, slots=True)
class NormalizationRecord:
    op_name: str
    input_span_ref: str
    before: str
    after: str
    reversible: bool
    provenance: str


@dataclass(frozen=True, slots=True)
class TokenAnchor:
    token_id: str
    raw_span: RawSpan
    raw_text: str
    normalized_text: str
    token_kind: TokenKind
    confidence: float


@dataclass(frozen=True, slots=True)
class SegmentAnchor:
    segment_id: str
    raw_span: RawSpan
    segment_kind: SegmentKind
    token_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class QuotedSpan:
    raw_span: RawSpan
    quote_kind: QuoteKind
    confidence: float


@dataclass(frozen=True, slots=True)
class InsertionSpan:
    raw_span: RawSpan
    insertion_kind: InsertionKind
    confidence: float


@dataclass(frozen=True, slots=True)
class SurfaceAmbiguity:
    ambiguity_kind: AmbiguityKind
    affected_span: RawSpan
    alternatives_ref: tuple[str, ...]
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class AlternativeSegmentation:
    alternative_id: str
    segments: tuple[SegmentAnchor, ...]
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class UtteranceSurface:
    epistemic_unit_ref: str
    raw_text: str
    tokens: tuple[TokenAnchor, ...]
    segments: tuple[SegmentAnchor, ...]
    quotes: tuple[QuotedSpan, ...]
    insertions: tuple[InsertionSpan, ...]
    normalization_log: tuple[NormalizationRecord, ...]
    ambiguities: tuple[SurfaceAmbiguity, ...]
    alternative_segmentations: tuple[AlternativeSegmentation, ...]
    reversible_span_map_present: bool


@dataclass(frozen=True, slots=True)
class SurfaceGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    surface_ref: str | None = None


@dataclass(frozen=True, slots=True)
class UtteranceSurfaceTelemetry:
    raw_length: int
    token_count: int
    segment_count: int
    quote_count: int
    insertion_count: int
    ambiguity_count: int
    normalization_ops: tuple[str, ...]
    surface_warnings: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    source_lineage: tuple[str, ...]
    produced_token_spans: tuple[tuple[str, int, int], ...]
    produced_segment_spans: tuple[tuple[str, int, int], ...]
    alternative_segmentation_count: int
    ambiguity_reasons: tuple[str, ...]
    downstream_gate: SurfaceGateDecision | None = None
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class UtteranceSurfaceResult:
    surface: UtteranceSurface
    telemetry: UtteranceSurfaceTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None

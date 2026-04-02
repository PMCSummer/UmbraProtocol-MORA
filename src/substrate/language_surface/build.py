from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import uuid4

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.epistemics import EpistemicUnit
from substrate.language_surface.models import (
    AlternativeSegmentation,
    AmbiguityKind,
    InsertionKind,
    InsertionSpan,
    NormalizationRecord,
    QuoteKind,
    QuotedSpan,
    RawSpan,
    SegmentAnchor,
    SegmentKind,
    SurfaceAmbiguity,
    TokenAnchor,
    TokenKind,
    UtteranceSurface,
    UtteranceSurfaceResult,
)
from substrate.language_surface.policy import evaluate_surface_downstream_gate
from substrate.language_surface.telemetry import (
    build_surface_telemetry,
    utterance_surface_result_snapshot,
)
from substrate.transition import execute_transition


TOKEN_PATTERN = re.compile(
    r"`[^`]+`|[A-Za-zА-Яа-яЁё0-9_]+(?:-[A-Za-zА-Яа-яЁё0-9_]+)?|\.{3}|[!?]+|[\"“”«»'`]|[(){}\[\],;:.—-]|[^\s]",
    flags=re.UNICODE,
)
WORD_PATTERN = re.compile(r"^[A-Za-zА-Яа-яЁё0-9_]+(?:-[A-Za-zА-Яа-яЁё0-9_]+)?$", flags=re.UNICODE)
ATTEMPTED_SURFACE_PATHS: tuple[str, ...] = (
    "surface.validate_input_shape",
    "surface.token_anchoring",
    "surface.segmentation",
    "surface.quote_detection",
    "surface.insertion_detection",
    "surface.normalization_log",
    "surface.ambiguity_and_alternatives",
    "surface.downstream_gate",
)


@dataclass(frozen=True, slots=True)
class SurfaceBuildContext:
    source_lineage: tuple[str, ...] = ()
    emit_alternative_segmentations: bool = True
    require_reversible_span_map: bool = True


def build_utterance_surface(
    epistemic_unit: EpistemicUnit,
    turn_metadata: dict[str, str] | None = None,
    context: SurfaceBuildContext | None = None,
) -> UtteranceSurfaceResult:
    if not isinstance(epistemic_unit, EpistemicUnit):
        raise TypeError("build_utterance_surface requires EpistemicUnit input from F02")

    context = context or SurfaceBuildContext()
    raw_text = epistemic_unit.content
    normalization_log = _build_normalization_log(raw_text)
    tokens = _build_token_anchors(raw_text)
    segments, segment_warnings = _segment_tokens(tokens, raw_text)
    quotes, quote_warnings = _detect_quoted_spans(raw_text)
    insertions, insertion_warnings = _detect_insertions(raw_text, tokens)
    ambiguities, alternatives, ambiguity_warnings = _derive_ambiguities_and_alternatives(
        raw_text=raw_text,
        tokens=tokens,
        base_segments=segments,
        context=context,
    )

    surface = UtteranceSurface(
        epistemic_unit_ref=epistemic_unit.unit_id,
        raw_text=raw_text,
        tokens=tokens,
        segments=segments,
        quotes=quotes,
        insertions=insertions,
        normalization_log=normalization_log,
        ambiguities=ambiguities,
        alternative_segmentations=alternatives,
        reversible_span_map_present=False,
    )
    reversible_span_map_present = _has_reversible_span_map(surface)
    surface = UtteranceSurface(
        epistemic_unit_ref=surface.epistemic_unit_ref,
        raw_text=surface.raw_text,
        tokens=surface.tokens,
        segments=surface.segments,
        quotes=surface.quotes,
        insertions=surface.insertions,
        normalization_log=surface.normalization_log,
        ambiguities=surface.ambiguities,
        alternative_segmentations=surface.alternative_segmentations,
        reversible_span_map_present=reversible_span_map_present,
    )
    _enforce_surface_invariants(surface)
    gate = evaluate_surface_downstream_gate(surface)

    source_lineage = tuple(
        x
        for x in (
            epistemic_unit.material_id,
            epistemic_unit.source_id,
            *context.source_lineage,
        )
        if x
    )
    warnings = tuple(
        dict.fromkeys(
            segment_warnings + quote_warnings + insertion_warnings + ambiguity_warnings
        )
    )
    telemetry = build_surface_telemetry(
        surface=surface,
        warnings=warnings,
        attempted_paths=ATTEMPTED_SURFACE_PATHS,
        source_lineage=source_lineage,
        downstream_gate=gate,
    )

    abstain = bool(
        (context.require_reversible_span_map and not surface.reversible_span_map_present)
        or not surface.tokens
        or not surface.segments
    )
    abstain_reason = None
    if abstain:
        if not surface.reversible_span_map_present:
            abstain_reason = "reversible span map invariant not satisfied"
        elif not surface.tokens:
            abstain_reason = "no token anchors produced"
        else:
            abstain_reason = "no segment anchors produced"

    partial_known = bool(surface.ambiguities or warnings)
    partial_known_reason = (
        "; ".join(ambiguity.reason for ambiguity in surface.ambiguities)
        if surface.ambiguities
        else ("; ".join(warnings) if warnings else None)
    )
    confidence = _estimate_result_confidence(surface=surface, warnings=warnings)

    _ = turn_metadata  # reserved for downstream turn stitching; not interpreted at L01
    return UtteranceSurfaceResult(
        surface=surface,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
    )


def surface_result_to_payload(result: UtteranceSurfaceResult) -> dict[str, object]:
    return utterance_surface_result_snapshot(result)


def persist_surface_result_via_f01(
    *,
    result: UtteranceSurfaceResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("l01-surface-build",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"surface-step-{transition_id}",
            "surface_snapshot": surface_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _build_normalization_log(raw_text: str) -> tuple[NormalizationRecord, ...]:
    records: list[NormalizationRecord] = []
    stripped = raw_text.strip()
    if stripped != raw_text:
        records.append(
            NormalizationRecord(
                op_name="trim_outer_whitespace_probe",
                input_span_ref="full-surface",
                before=raw_text,
                after=stripped,
                reversible=True,
                provenance="safe probe normalization; raw text preserved in surface.raw_text",
            )
        )
    else:
        records.append(
            NormalizationRecord(
                op_name="identity_passthrough",
                input_span_ref="full-surface",
                before=raw_text,
                after=raw_text,
                reversible=True,
                provenance="no destructive normalization applied",
            )
        )
    return tuple(records)


def _build_token_anchors(raw_text: str) -> tuple[TokenAnchor, ...]:
    tokens: list[TokenAnchor] = []
    for match in TOKEN_PATTERN.finditer(raw_text):
        token_text = match.group(0)
        token_kind = _classify_token_kind(token_text)
        token_id = f"tok-{uuid4().hex[:10]}"
        confidence = _token_confidence(token_kind)
        span = RawSpan(
            start=match.start(),
            end=match.end(),
            raw_text=raw_text[match.start() : match.end()],
        )
        tokens.append(
            TokenAnchor(
                token_id=token_id,
                raw_span=span,
                raw_text=token_text,
                normalized_text=token_text,
                token_kind=token_kind,
                confidence=confidence,
            )
        )
    if not tokens and raw_text:
        # Keep non-empty noisy/whitespace-only payloads inspectable instead of failing hard.
        span = RawSpan(start=0, end=len(raw_text), raw_text=raw_text)
        tokens.append(
            TokenAnchor(
                token_id=f"tok-{uuid4().hex[:10]}",
                raw_span=span,
                raw_text=raw_text,
                normalized_text=raw_text,
                token_kind=TokenKind.UNKNOWN,
                confidence=0.35,
            )
        )
    return tuple(tokens)


def _segment_tokens(
    tokens: tuple[TokenAnchor, ...], raw_text: str
) -> tuple[tuple[SegmentAnchor, ...], tuple[str, ...]]:
    if not tokens:
        return (), ("no_token_anchors",)

    segments: list[SegmentAnchor] = []
    warnings: list[str] = []
    current_token_ids: list[str] = []
    current_tokens: list[TokenAnchor] = []

    def flush(kind: SegmentKind, confidence: float) -> None:
        if not current_tokens:
            return
        first = current_tokens[0].raw_span.start
        last = current_tokens[-1].raw_span.end
        span = RawSpan(start=first, end=last, raw_text=raw_text[first:last])
        segments.append(
            SegmentAnchor(
                segment_id=f"seg-{uuid4().hex[:10]}",
                raw_span=span,
                segment_kind=kind,
                token_ids=tuple(current_token_ids),
                confidence=confidence,
            )
        )
        current_tokens.clear()
        current_token_ids.clear()

    for token in tokens:
        current_tokens.append(token)
        current_token_ids.append(token.token_id)
        if token.raw_text in {".", "!", "?"}:
            flush(SegmentKind.SENTENCE, 0.95)
        elif token.raw_text in {";", ":"}:
            flush(SegmentKind.CLAUSE, 0.85)

    if current_tokens:
        warnings.append("terminal_boundary_missing")
        flush(SegmentKind.UNKNOWN, 0.65)

    return tuple(segments), tuple(warnings)


def _detect_quoted_spans(raw_text: str) -> tuple[tuple[QuotedSpan, ...], tuple[str, ...]]:
    quoted: list[QuotedSpan] = []
    warnings: list[str] = []
    patterns = (
        (QuoteKind.DOUBLE, re.compile(r"\"([^\"]+)\"")),
        (QuoteKind.ANGLED, re.compile(r"«([^»]+)»")),
        (QuoteKind.SINGLE, re.compile(r"'([^']+)'")),
    )
    for kind, pattern in patterns:
        for match in pattern.finditer(raw_text):
            start = match.start()
            end = match.end()
            quoted.append(
                QuotedSpan(
                    raw_span=RawSpan(start=start, end=end, raw_text=raw_text[start:end]),
                    quote_kind=kind,
                    confidence=0.9,
                )
            )

    double_count = raw_text.count('"')
    angled_open_count = raw_text.count("«")
    angled_close_count = raw_text.count("»")
    if double_count % 2 != 0 or angled_open_count != angled_close_count:
        warnings.append("quote_boundary_uncertain")
    return tuple(quoted), tuple(warnings)


def _detect_insertions(
    raw_text: str, tokens: tuple[TokenAnchor, ...]
) -> tuple[tuple[InsertionSpan, ...], tuple[str, ...]]:
    insertions: list[InsertionSpan] = []
    warnings: list[str] = []
    seen: set[tuple[int, int, InsertionKind]] = set()

    for match in re.finditer(r"\([^)]*\)", raw_text):
        key = (match.start(), match.end(), InsertionKind.PARENTHETICAL)
        if key in seen:
            continue
        seen.add(key)
        insertions.append(
            InsertionSpan(
                raw_span=RawSpan(match.start(), match.end(), raw_text[match.start() : match.end()]),
                insertion_kind=InsertionKind.PARENTHETICAL,
                confidence=0.92,
            )
        )

    for match in re.finditer(r"`[^`]+`", raw_text):
        key = (match.start(), match.end(), InsertionKind.CODE)
        if key in seen:
            continue
        seen.add(key)
        insertions.append(
            InsertionSpan(
                raw_span=RawSpan(match.start(), match.end(), raw_text[match.start() : match.end()]),
                insertion_kind=InsertionKind.CODE,
                confidence=0.9,
            )
        )

    for token in tokens:
        if token.token_kind in {TokenKind.REPAIR_FRAGMENT, TokenKind.ELLIPSIS}:
            key = (token.raw_span.start, token.raw_span.end, InsertionKind.REPAIR_FRAGMENT)
            if key in seen:
                continue
            seen.add(key)
            insertions.append(
                InsertionSpan(
                    raw_span=token.raw_span,
                    insertion_kind=InsertionKind.REPAIR_FRAGMENT,
                    confidence=0.72,
                )
            )

    if re.search(r"\s{2,}", raw_text):
        warnings.append("noisy_separator_detected")
    return tuple(insertions), tuple(warnings)


def _derive_ambiguities_and_alternatives(
    *,
    raw_text: str,
    tokens: tuple[TokenAnchor, ...],
    base_segments: tuple[SegmentAnchor, ...],
    context: SurfaceBuildContext,
) -> tuple[tuple[SurfaceAmbiguity, ...], tuple[AlternativeSegmentation, ...], tuple[str, ...]]:
    ambiguities: list[SurfaceAmbiguity] = []
    warnings: list[str] = []
    alternatives: list[AlternativeSegmentation] = []
    alternative_ids: list[str] = []

    ellipsis_tokens = tuple(token for token in tokens if token.raw_text == "...")
    punct_clusters = tuple(
        token for token in tokens if re.fullmatch(r"[!?]{2,}", token.raw_text) is not None
    )

    if ellipsis_tokens and context.emit_alternative_segmentations:
        alt_segments = _segment_with_ellipsis_boundaries(tokens=tokens, raw_text=raw_text)
        alt_id = f"alt-{uuid4().hex[:8]}"
        alternatives.append(
            AlternativeSegmentation(
                alternative_id=alt_id,
                segments=alt_segments,
                confidence=0.62,
                reason="ellipsis can mark pause, repair, or boundary",
            )
        )
        alternative_ids.append(alt_id)
        for token in ellipsis_tokens:
            ambiguities.append(
                SurfaceAmbiguity(
                    ambiguity_kind=AmbiguityKind.BOUNDARY_UNCERTAIN_ELLIPSIS,
                    affected_span=token.raw_span,
                    alternatives_ref=(alt_id,),
                    confidence=0.66,
                    reason="ellipsis boundary can be interpreted as split or continuation",
                )
            )

    if punct_clusters:
        alternatives_ref = tuple(alternative_ids)
        for token in punct_clusters:
            ambiguities.append(
                SurfaceAmbiguity(
                    ambiguity_kind=AmbiguityKind.BOUNDARY_UNCERTAIN_PUNCT_CLUSTER,
                    affected_span=token.raw_span,
                    alternatives_ref=alternatives_ref,
                    confidence=0.61,
                    reason="punctuation cluster yields unstable segmentation boundary",
                )
            )
        warnings.append("punctuation_cluster_ambiguous")

    if raw_text and raw_text[-1] not in ".!?":
        span = RawSpan(start=max(0, len(raw_text) - 1), end=len(raw_text), raw_text=raw_text[-1:])
        ambiguities.append(
            SurfaceAmbiguity(
                ambiguity_kind=AmbiguityKind.TERMINAL_BOUNDARY_MISSING,
                affected_span=span,
                alternatives_ref=tuple(alternative_ids),
                confidence=0.58,
                reason="missing terminal punctuation leaves boundary underspecified",
            )
        )

    if raw_text.count('"') % 2 != 0 or raw_text.count("«") != raw_text.count("»"):
        ambiguities.append(
            SurfaceAmbiguity(
                ambiguity_kind=AmbiguityKind.QUOTE_BOUNDARY_UNCERTAIN,
                affected_span=RawSpan(start=0, end=len(raw_text), raw_text=raw_text),
                alternatives_ref=tuple(alternative_ids),
                confidence=0.55,
                reason="unbalanced quote markers",
            )
        )
        warnings.append("quote_boundary_uncertain")

    if raw_text.count("(") != raw_text.count(")"):
        ambiguities.append(
            SurfaceAmbiguity(
                ambiguity_kind=AmbiguityKind.NOISY_SEPARATOR,
                affected_span=RawSpan(start=0, end=len(raw_text), raw_text=raw_text),
                alternatives_ref=tuple(alternative_ids),
                confidence=0.53,
                reason="unbalanced parenthetical markers",
            )
        )
        warnings.append("parenthetical_boundary_uncertain")

    if raw_text.count("`") % 2 != 0:
        ambiguities.append(
            SurfaceAmbiguity(
                ambiguity_kind=AmbiguityKind.NOISY_SEPARATOR,
                affected_span=RawSpan(start=0, end=len(raw_text), raw_text=raw_text),
                alternatives_ref=tuple(alternative_ids),
                confidence=0.52,
                reason="unbalanced code marker",
            )
        )
        warnings.append("code_span_boundary_uncertain")

    if re.search(r"\s{2,}", raw_text):
        ambiguities.append(
            SurfaceAmbiguity(
                ambiguity_kind=AmbiguityKind.NOISY_SEPARATOR,
                affected_span=RawSpan(start=0, end=len(raw_text), raw_text=raw_text),
                alternatives_ref=tuple(alternative_ids),
                confidence=0.57,
                reason="noisy duplicated separators may shift boundary confidence",
            )
        )

    if context.emit_alternative_segmentations and ambiguities and not alternatives:
        alt_id = f"alt-{uuid4().hex[:8]}"
        alternatives.append(
            AlternativeSegmentation(
                alternative_id=alt_id,
                segments=base_segments,
                confidence=0.51,
                reason="surface ambiguity present without strong alternative split",
            )
        )
        for idx, ambiguity in enumerate(ambiguities):
            ambiguities[idx] = SurfaceAmbiguity(
                ambiguity_kind=ambiguity.ambiguity_kind,
                affected_span=ambiguity.affected_span,
                alternatives_ref=(alt_id,),
                confidence=ambiguity.confidence,
                reason=ambiguity.reason,
            )

    return tuple(ambiguities), tuple(alternatives), tuple(dict.fromkeys(warnings))


def _segment_with_ellipsis_boundaries(
    *, tokens: tuple[TokenAnchor, ...], raw_text: str
) -> tuple[SegmentAnchor, ...]:
    segments: list[SegmentAnchor] = []
    current_tokens: list[TokenAnchor] = []
    current_ids: list[str] = []

    def flush(kind: SegmentKind, confidence: float) -> None:
        if not current_tokens:
            return
        start = current_tokens[0].raw_span.start
        end = current_tokens[-1].raw_span.end
        segments.append(
            SegmentAnchor(
                segment_id=f"seg-alt-{uuid4().hex[:8]}",
                raw_span=RawSpan(start=start, end=end, raw_text=raw_text[start:end]),
                segment_kind=kind,
                token_ids=tuple(current_ids),
                confidence=confidence,
            )
        )
        current_tokens.clear()
        current_ids.clear()

    for token in tokens:
        current_tokens.append(token)
        current_ids.append(token.token_id)
        if token.raw_text in {".", "!", "?", "..."}:
            flush(SegmentKind.SENTENCE, 0.7 if token.raw_text == "..." else 0.9)
    if current_tokens:
        flush(SegmentKind.UNKNOWN, 0.6)
    return tuple(segments)


def _classify_token_kind(token_text: str) -> TokenKind:
    if token_text.startswith("`") and token_text.endswith("`") and len(token_text) >= 2:
        return TokenKind.CODE_LITERAL
    if token_text == "...":
        return TokenKind.ELLIPSIS
    if token_text in {'"', "'", "«", "»", "“", "”"}:
        return TokenKind.QUOTE_MARK
    if WORD_PATTERN.fullmatch(token_text):
        if _looks_like_repair_fragment(token_text):
            return TokenKind.REPAIR_FRAGMENT
        return TokenKind.WORD
    if re.fullmatch(r"[(){}\[\],;:.!?—-]+", token_text):
        return TokenKind.PUNCTUATION
    return TokenKind.UNKNOWN


def _looks_like_repair_fragment(token_text: str) -> bool:
    if "-" not in token_text:
        return False
    left, right = token_text.split("-", 1)
    if not left or not right:
        return False
    return (len(left) <= 3 and len(right) <= 3) or left == right


def _token_confidence(token_kind: TokenKind) -> float:
    if token_kind == TokenKind.WORD:
        return 0.95
    if token_kind == TokenKind.PUNCTUATION:
        return 0.99
    if token_kind == TokenKind.QUOTE_MARK:
        return 0.97
    if token_kind == TokenKind.ELLIPSIS:
        return 0.82
    if token_kind == TokenKind.CODE_LITERAL:
        return 0.9
    if token_kind == TokenKind.REPAIR_FRAGMENT:
        return 0.74
    return 0.5


def _has_reversible_span_map(surface: UtteranceSurface) -> bool:
    raw_text = surface.raw_text
    token_map = {token.token_id: token for token in surface.tokens}
    if not token_map and raw_text == "" and not surface.segments:
        return True
    if not token_map:
        return False
    for token in surface.tokens:
        if token.raw_span.start < 0 or token.raw_span.end > len(raw_text):
            return False
        if token.raw_span.start >= token.raw_span.end:
            return False
        if raw_text[token.raw_span.start : token.raw_span.end] != token.raw_span.raw_text:
            return False
    for segment in surface.segments:
        if segment.raw_span.start < 0 or segment.raw_span.end > len(raw_text):
            return False
        if segment.raw_span.start >= segment.raw_span.end:
            return False
        if any(token_id not in token_map for token_id in segment.token_ids):
            return False
    return True


def _enforce_surface_invariants(surface: UtteranceSurface) -> None:
    if not surface.normalization_log:
        raise ValueError("normalization log is mandatory for L01 surface")
    if not surface.reversible_span_map_present:
        raise ValueError("reversible span map is mandatory for L01 surface")
    for token in surface.tokens:
        if token.raw_span.raw_text != token.raw_text:
            raise ValueError("token raw text must be consistent with raw span")
    for segment in surface.segments:
        if not segment.token_ids:
            raise ValueError("segment must contain token ids")
    # L01 must preserve ambiguity as state, not hide unstable boundaries.
    if any(token.raw_text == "..." for token in surface.tokens) and not surface.ambiguities:
        raise ValueError("ellipsis without ambiguity state violates L01 claim boundary")


def _estimate_result_confidence(
    *, surface: UtteranceSurface, warnings: tuple[str, ...]
) -> float:
    score = 0.92
    score -= min(0.5, len(surface.ambiguities) * 0.08)
    score -= min(0.25, len(warnings) * 0.04)
    if not surface.quotes and '"' in surface.raw_text:
        score -= 0.08
    if not surface.reversible_span_map_present:
        score -= 0.4
    return max(0.05, min(0.99, round(score, 4)))

from __future__ import annotations

from substrate.language_surface.models import (
    SurfaceGateDecision,
    UtteranceSurface,
    UtteranceSurfaceResult,
    UtteranceSurfaceTelemetry,
)


def build_surface_telemetry(
    *,
    surface: UtteranceSurface,
    warnings: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    source_lineage: tuple[str, ...],
    downstream_gate: SurfaceGateDecision | None,
) -> UtteranceSurfaceTelemetry:
    return UtteranceSurfaceTelemetry(
        raw_length=len(surface.raw_text),
        token_count=len(surface.tokens),
        segment_count=len(surface.segments),
        quote_count=len(surface.quotes),
        insertion_count=len(surface.insertions),
        ambiguity_count=len(surface.ambiguities),
        normalization_ops=tuple(record.op_name for record in surface.normalization_log),
        surface_warnings=warnings,
        attempted_paths=attempted_paths,
        source_lineage=source_lineage,
        produced_token_spans=tuple(
            (token.token_id, token.raw_span.start, token.raw_span.end) for token in surface.tokens
        ),
        produced_segment_spans=tuple(
            (segment.segment_id, segment.raw_span.start, segment.raw_span.end)
            for segment in surface.segments
        ),
        alternative_segmentation_count=len(surface.alternative_segmentations),
        ambiguity_reasons=tuple(ambiguity.reason for ambiguity in surface.ambiguities),
        downstream_gate=downstream_gate,
    )


def utterance_surface_result_snapshot(result: UtteranceSurfaceResult) -> dict[str, object]:
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "surface": {
            "epistemic_unit_ref": result.surface.epistemic_unit_ref,
            "raw_text": result.surface.raw_text,
            "token_count": len(result.surface.tokens),
            "segment_count": len(result.surface.segments),
            "quote_count": len(result.surface.quotes),
            "insertion_count": len(result.surface.insertions),
            "ambiguity_count": len(result.surface.ambiguities),
            "alternative_segmentation_count": len(result.surface.alternative_segmentations),
            "reversible_span_map_present": result.surface.reversible_span_map_present,
            "tokens": tuple(
                {
                    "token_id": token.token_id,
                    "span": (token.raw_span.start, token.raw_span.end),
                    "raw_text": token.raw_text,
                    "normalized_text": token.normalized_text,
                    "token_kind": token.token_kind.value,
                    "confidence": token.confidence,
                }
                for token in result.surface.tokens
            ),
            "segments": tuple(
                {
                    "segment_id": segment.segment_id,
                    "span": (segment.raw_span.start, segment.raw_span.end),
                    "segment_kind": segment.segment_kind.value,
                    "token_ids": segment.token_ids,
                    "confidence": segment.confidence,
                }
                for segment in result.surface.segments
            ),
            "quotes": tuple(
                {
                    "span": (quote.raw_span.start, quote.raw_span.end),
                    "raw_text": quote.raw_span.raw_text,
                    "quote_kind": quote.quote_kind.value,
                    "confidence": quote.confidence,
                }
                for quote in result.surface.quotes
            ),
            "insertions": tuple(
                {
                    "span": (insertion.raw_span.start, insertion.raw_span.end),
                    "raw_text": insertion.raw_span.raw_text,
                    "insertion_kind": insertion.insertion_kind.value,
                    "confidence": insertion.confidence,
                }
                for insertion in result.surface.insertions
            ),
            "normalization_log": tuple(
                {
                    "op_name": record.op_name,
                    "input_span_ref": record.input_span_ref,
                    "before": record.before,
                    "after": record.after,
                    "reversible": record.reversible,
                    "provenance": record.provenance,
                }
                for record in result.surface.normalization_log
            ),
            "ambiguities": tuple(
                {
                    "ambiguity_kind": ambiguity.ambiguity_kind.value,
                    "span": (
                        ambiguity.affected_span.start,
                        ambiguity.affected_span.end,
                    ),
                    "raw_text": ambiguity.affected_span.raw_text,
                    "alternatives_ref": ambiguity.alternatives_ref,
                    "confidence": ambiguity.confidence,
                    "reason": ambiguity.reason,
                }
                for ambiguity in result.surface.ambiguities
            ),
            "alternative_segmentations": tuple(
                {
                    "alternative_id": alternative.alternative_id,
                    "confidence": alternative.confidence,
                    "reason": alternative.reason,
                    "segments": tuple(
                        {
                            "segment_id": seg.segment_id,
                            "span": (seg.raw_span.start, seg.raw_span.end),
                            "segment_kind": seg.segment_kind.value,
                            "token_ids": seg.token_ids,
                            "confidence": seg.confidence,
                        }
                        for seg in alternative.segments
                    ),
                }
                for alternative in result.surface.alternative_segmentations
            ),
        },
        "telemetry": {
            "raw_length": result.telemetry.raw_length,
            "normalization_ops": result.telemetry.normalization_ops,
            "surface_warnings": result.telemetry.surface_warnings,
            "attempted_paths": result.telemetry.attempted_paths,
            "source_lineage": result.telemetry.source_lineage,
            "downstream_gate": (
                {
                    "accepted": result.telemetry.downstream_gate.accepted,
                    "restrictions": result.telemetry.downstream_gate.restrictions,
                    "reason": result.telemetry.downstream_gate.reason,
                }
                if result.telemetry.downstream_gate is not None
                else None
            ),
        },
    }

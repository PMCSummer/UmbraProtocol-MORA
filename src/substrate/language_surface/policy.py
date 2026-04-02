from __future__ import annotations

from substrate.language_surface.models import SurfaceGateDecision, UtteranceSurface


def evaluate_surface_downstream_gate(surface_or_other: object) -> SurfaceGateDecision:
    if not isinstance(surface_or_other, UtteranceSurface):
        raise TypeError("downstream surface gate requires typed UtteranceSurface input")

    surface = surface_or_other
    restrictions: list[str] = []

    if not surface.reversible_span_map_present:
        restrictions.append("reversible_span_map_missing")
    if surface.ambiguities:
        restrictions.append("surface_ambiguity_present")
    if surface.quotes:
        restrictions.append("quoted_spans_present")
    if surface.insertions:
        restrictions.append("insertion_spans_present")
    if surface.normalization_log:
        restrictions.append("normalization_log_present")
    if not surface.tokens:
        restrictions.append("token_anchors_missing")
    if not surface.segments:
        restrictions.append("segment_anchors_missing")

    accepted = (
        surface.reversible_span_map_present
        and bool(surface.tokens)
        and bool(surface.segments)
    )
    if accepted:
        reason = "typed surface accepted for downstream language contour"
    else:
        reason = "typed surface rejected due to missing load-bearing anchors"

    return SurfaceGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        surface_ref=surface.epistemic_unit_ref,
    )

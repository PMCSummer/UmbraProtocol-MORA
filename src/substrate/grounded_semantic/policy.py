from __future__ import annotations

from substrate.grounded_semantic.models import (
    GroundedSemanticBundle,
    GroundedSemanticGateDecision,
    GroundedSemanticResult,
)


def evaluate_grounded_semantic_downstream_gate(
    grounded_result_or_bundle: object,
) -> GroundedSemanticGateDecision:
    if isinstance(grounded_result_or_bundle, GroundedSemanticResult):
        bundle = grounded_result_or_bundle.bundle
    elif isinstance(grounded_result_or_bundle, GroundedSemanticBundle):
        bundle = grounded_result_or_bundle
    else:
        raise TypeError(
            "grounded semantic gate requires typed GroundedSemanticResult/GroundedSemanticBundle"
        )

    restrictions: list[str] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    if bundle.no_final_semantic_resolution:
        restrictions.append("no_final_semantic_resolution")
    if bundle.uncertainty_markers:
        restrictions.append("uncertainty_markers_present")
    if bundle.ambiguity_reasons:
        restrictions.append("ambiguity_present")
    if bundle.low_coverage_mode:
        restrictions.append("low_coverage_mode")
    if not bundle.operator_carriers:
        restrictions.append("operator_carriers_sparse")
    if not bundle.source_anchors:
        restrictions.append("source_anchors_sparse")
    if not bundle.modus_carriers:
        restrictions.append("modus_carriers_sparse")
    if bundle.low_coverage_mode or not bundle.operator_carriers or not bundle.source_anchors:
        restrictions.append("downstream_authority_degraded")

    for scaffold in bundle.phrase_scaffolds:
        if scaffold.confidence >= 0.2:
            accepted_ids.append(scaffold.scaffold_id)
        else:
            rejected_ids.append(scaffold.scaffold_id)

    accepted = bool(bundle.phrase_scaffolds and bundle.dictum_carriers)
    if not accepted:
        restrictions.append("no_usable_scaffold")
        reason = "grounded semantic bundle has no usable phrase scaffold"
    else:
        reason = "typed grounded semantic scaffold emitted with bounded restrictions"

    return GroundedSemanticGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_scaffold_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_scaffold_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_dictum_ref,
    )

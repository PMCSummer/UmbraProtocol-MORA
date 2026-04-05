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
    if bundle.normative_l05_l06_route_active:
        restrictions.append("normative_l05_l06_route_active")
        restrictions.append("source_modus_ref_class_must_be_read")
        restrictions.append("source_discourse_update_ref_class_must_be_read")
        restrictions.append("phase_native_source_refs_required_on_normative_route")
    if bundle.legacy_surface_cue_fallback_used:
        restrictions.append("legacy_surface_cue_fallback_used")
        restrictions.append("legacy_source_lineage_mode")
    if bundle.legacy_surface_cue_path_not_normative:
        restrictions.append("legacy_surface_cue_path_not_normative")
    if bundle.l04_only_input_not_equivalent_to_l05_l06_route:
        restrictions.append("l04_only_input_not_equivalent_to_l05_l06_route")
    if bundle.discourse_update_not_inferred_from_surface_when_l06_available:
        restrictions.append("discourse_update_not_inferred_from_surface_when_l06_available")
    if bundle.l06_blocked_update_present:
        restrictions.append("l06_blocked_update_present")
    if bundle.l06_guarded_continue_present:
        restrictions.append("l06_guarded_continue_present")
    if not bundle.operator_carriers:
        restrictions.append("operator_carriers_sparse")
    if not bundle.source_anchors:
        restrictions.append("source_anchors_sparse")
    if not bundle.modus_carriers:
        restrictions.append("modus_carriers_sparse")

    source_ref_shape_gap = False
    if bundle.normative_l05_l06_route_active:
        if not bundle.source_modus_ref or not bundle.source_discourse_update_ref:
            source_ref_shape_gap = True
        if bundle.source_modus_ref_kind != "phase_native_derived_ref":
            source_ref_shape_gap = True
        if bundle.source_discourse_update_ref_kind != "phase_native_derived_ref":
            source_ref_shape_gap = True
        if (
            bundle.source_modus_lineage_ref
            and bundle.source_modus_ref == bundle.source_modus_lineage_ref
        ):
            source_ref_shape_gap = True
        if (
            bundle.source_discourse_update_lineage_ref
            and bundle.source_discourse_update_ref == bundle.source_discourse_update_lineage_ref
        ):
            source_ref_shape_gap = True
    if bundle.legacy_surface_cue_fallback_used:
        if bundle.source_modus_ref or bundle.source_discourse_update_ref:
            source_ref_shape_gap = True
    if source_ref_shape_gap:
        restrictions.append("source_ref_relabeling_without_notice")
    if (
        bundle.low_coverage_mode
        or not bundle.operator_carriers
        or not bundle.source_anchors
        or bundle.legacy_surface_cue_fallback_used
        or bundle.l06_blocked_update_present
        or bundle.l06_guarded_continue_present
        or source_ref_shape_gap
    ):
        restrictions.append("downstream_authority_degraded")
    if bundle.legacy_surface_cue_fallback_used:
        restrictions.append("legacy_fallback_requires_degraded_contract")

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

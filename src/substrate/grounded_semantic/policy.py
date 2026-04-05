from __future__ import annotations

from substrate.grounded_semantic.models import (
    G01RestrictionCode,
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
        restrictions.append(G01RestrictionCode.NO_FINAL_SEMANTIC_RESOLUTION)
    if bundle.uncertainty_markers:
        restrictions.append(G01RestrictionCode.UNCERTAINTY_MARKERS_PRESENT)
    if bundle.ambiguity_reasons:
        restrictions.append(G01RestrictionCode.AMBIGUITY_PRESENT)
    if bundle.low_coverage_mode:
        restrictions.append(G01RestrictionCode.LOW_COVERAGE_MODE)
    if bundle.normative_l05_l06_route_active:
        restrictions.append(G01RestrictionCode.NORMATIVE_L05_L06_ROUTE_ACTIVE)
        restrictions.append(G01RestrictionCode.SOURCE_MODUS_REF_CLASS_MUST_BE_READ)
        restrictions.append(
            G01RestrictionCode.SOURCE_DISCOURSE_UPDATE_REF_CLASS_MUST_BE_READ
        )
        restrictions.append(
            G01RestrictionCode.PHASE_NATIVE_SOURCE_REFS_REQUIRED_ON_NORMATIVE_ROUTE
        )
    if bundle.legacy_surface_cue_fallback_used:
        restrictions.append(G01RestrictionCode.LEGACY_SURFACE_CUE_FALLBACK_USED)
        restrictions.append(G01RestrictionCode.LEGACY_SOURCE_LINEAGE_MODE)
    if bundle.legacy_surface_cue_path_not_normative:
        restrictions.append(G01RestrictionCode.LEGACY_SURFACE_CUE_PATH_NOT_NORMATIVE)
    if bundle.l04_only_input_not_equivalent_to_l05_l06_route:
        restrictions.append(
            G01RestrictionCode.L04_ONLY_INPUT_NOT_EQUIVALENT_TO_L05_L06_ROUTE
        )
    if bundle.discourse_update_not_inferred_from_surface_when_l06_available:
        restrictions.append(
            G01RestrictionCode.DISCOURSE_UPDATE_NOT_INFERRED_FROM_SURFACE_WHEN_L06_AVAILABLE
        )
    if bundle.l06_blocked_update_present:
        restrictions.append(G01RestrictionCode.L06_BLOCKED_UPDATE_PRESENT)
    if bundle.l06_guarded_continue_present:
        restrictions.append(G01RestrictionCode.L06_GUARDED_CONTINUE_PRESENT)
    if not bundle.operator_carriers:
        restrictions.append(G01RestrictionCode.OPERATOR_CARRIERS_SPARSE)
    if not bundle.source_anchors:
        restrictions.append(G01RestrictionCode.SOURCE_ANCHORS_SPARSE)
    if not bundle.modus_carriers:
        restrictions.append(G01RestrictionCode.MODUS_CARRIERS_SPARSE)

    source_ref_shape_gap = False
    evidence_factorization_gap = False
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
    if not bundle.evidence_records:
        evidence_factorization_gap = True
    if bundle.normative_l05_l06_route_active and not any(
        record.route_class == "normative" for record in bundle.evidence_records
    ):
        evidence_factorization_gap = True
    if bundle.legacy_surface_cue_fallback_used and not any(
        record.route_class == "compatibility" for record in bundle.evidence_records
    ):
        evidence_factorization_gap = True
    if source_ref_shape_gap:
        restrictions.append(G01RestrictionCode.SOURCE_REF_RELABELING_WITHOUT_NOTICE)
    if evidence_factorization_gap:
        restrictions.append(G01RestrictionCode.EVIDENCE_FACTORIZATION_GAP)
    if (
        bundle.low_coverage_mode
        or not bundle.operator_carriers
        or not bundle.source_anchors
        or bundle.legacy_surface_cue_fallback_used
        or bundle.l06_blocked_update_present
        or bundle.l06_guarded_continue_present
        or source_ref_shape_gap
        or evidence_factorization_gap
    ):
        restrictions.append(G01RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
    if bundle.legacy_surface_cue_fallback_used:
        restrictions.append(
            G01RestrictionCode.LEGACY_FALLBACK_REQUIRES_DEGRADED_CONTRACT
        )

    for scaffold in bundle.phrase_scaffolds:
        if scaffold.confidence >= 0.2:
            accepted_ids.append(scaffold.scaffold_id)
        else:
            rejected_ids.append(scaffold.scaffold_id)

    accepted = bool(bundle.phrase_scaffolds and bundle.dictum_carriers)
    if not accepted:
        restrictions.append(G01RestrictionCode.NO_USABLE_SCAFFOLD)
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

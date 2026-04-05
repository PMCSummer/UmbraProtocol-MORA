from __future__ import annotations

from substrate.grounded_semantic.models import (
    GroundedSemanticBundle,
    GroundedSemanticGateDecision,
    GroundedSemanticResult,
    GroundedSemanticTelemetry,
)


def build_grounded_semantic_telemetry(
    *,
    bundle: GroundedSemanticBundle,
    source_lineage: tuple[str, ...],
    reversible_span_mapping_present: bool,
    attempted_paths: tuple[str, ...],
    downstream_gate: GroundedSemanticGateDecision,
    causal_basis: str,
) -> GroundedSemanticTelemetry:
    return GroundedSemanticTelemetry(
        source_lineage=source_lineage,
        source_dictum_ref=bundle.source_dictum_ref,
        source_syntax_ref=bundle.source_syntax_ref,
        source_surface_ref=bundle.source_surface_ref,
        source_modus_ref=bundle.source_modus_ref,
        source_modus_ref_kind=bundle.source_modus_ref_kind,
        source_modus_lineage_ref=bundle.source_modus_lineage_ref,
        source_discourse_update_ref=bundle.source_discourse_update_ref,
        source_discourse_update_ref_kind=bundle.source_discourse_update_ref_kind,
        source_discourse_update_lineage_ref=bundle.source_discourse_update_lineage_ref,
        substrate_unit_count=len(bundle.substrate_units),
        phrase_scaffold_count=len(bundle.phrase_scaffolds),
        operator_carrier_count=len(bundle.operator_carriers),
        dictum_carrier_count=len(bundle.dictum_carriers),
        modus_carrier_count=len(bundle.modus_carriers),
        source_anchor_count=len(bundle.source_anchors),
        uncertainty_marker_count=len(bundle.uncertainty_markers),
        operator_kinds=tuple(dict.fromkeys(carrier.operator_kind.value for carrier in bundle.operator_carriers)),
        uncertainty_kinds=tuple(dict.fromkeys(marker.uncertainty_kind.value for marker in bundle.uncertainty_markers)),
        reversible_span_mapping_present=reversible_span_mapping_present,
        low_coverage_mode=bundle.low_coverage_mode,
        low_coverage_reasons=bundle.low_coverage_reasons,
        ambiguity_reasons=bundle.ambiguity_reasons,
        normative_l05_l06_route_active=bundle.normative_l05_l06_route_active,
        legacy_surface_cue_fallback_used=bundle.legacy_surface_cue_fallback_used,
        l06_blocked_update_present=bundle.l06_blocked_update_present,
        l06_guarded_continue_present=bundle.l06_guarded_continue_present,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def grounded_semantic_result_snapshot(result: GroundedSemanticResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_final_semantic_resolution": result.no_final_semantic_resolution,
        "bundle": {
            "source_dictum_ref": bundle.source_dictum_ref,
            "source_syntax_ref": bundle.source_syntax_ref,
            "source_surface_ref": bundle.source_surface_ref,
            "source_modus_ref": bundle.source_modus_ref,
            "source_modus_ref_kind": bundle.source_modus_ref_kind,
            "source_modus_lineage_ref": bundle.source_modus_lineage_ref,
            "source_discourse_update_ref": bundle.source_discourse_update_ref,
            "source_discourse_update_ref_kind": bundle.source_discourse_update_ref_kind,
            "source_discourse_update_lineage_ref": bundle.source_discourse_update_lineage_ref,
            "linked_dictum_candidate_ids": bundle.linked_dictum_candidate_ids,
            "linked_modus_record_ids": bundle.linked_modus_record_ids,
            "linked_update_proposal_ids": bundle.linked_update_proposal_ids,
            "low_coverage_mode": bundle.low_coverage_mode,
            "low_coverage_reasons": bundle.low_coverage_reasons,
            "ambiguity_reasons": bundle.ambiguity_reasons,
            "normative_l05_l06_route_active": bundle.normative_l05_l06_route_active,
            "legacy_surface_cue_fallback_used": bundle.legacy_surface_cue_fallback_used,
            "legacy_surface_cue_path_not_normative": bundle.legacy_surface_cue_path_not_normative,
            "l04_only_input_not_equivalent_to_l05_l06_route": bundle.l04_only_input_not_equivalent_to_l05_l06_route,
            "discourse_update_not_inferred_from_surface_when_l06_available": bundle.discourse_update_not_inferred_from_surface_when_l06_available,
            "l06_blocked_update_present": bundle.l06_blocked_update_present,
            "l06_guarded_continue_present": bundle.l06_guarded_continue_present,
            "no_final_semantic_resolution": bundle.no_final_semantic_resolution,
            "reason": bundle.reason,
            "substrate_units": tuple(
                {
                    "unit_id": unit.unit_id,
                    "span_start": unit.span_start,
                    "span_end": unit.span_end,
                    "raw_surface": unit.raw_surface,
                    "normalized_form": unit.normalized_form,
                    "unit_kind": unit.unit_kind.value,
                    "channel_origin": unit.channel_origin.value,
                    "confidence": unit.confidence,
                    "provenance": unit.provenance,
                    "ambiguity_state": unit.ambiguity_state.value,
                }
                for unit in bundle.substrate_units
            ),
            "phrase_scaffolds": tuple(
                {
                    "scaffold_id": scaffold.scaffold_id,
                    "clause_boundaries": tuple((b.start, b.end) for b in scaffold.clause_boundaries),
                    "phrase_boundaries": tuple((b.start, b.end) for b in scaffold.phrase_boundaries),
                    "operator_attachments": tuple(
                        {
                            "operator_id": attachment.operator_id,
                            "target_ref": attachment.target_ref,
                            "relation": attachment.relation,
                            "unresolved": attachment.unresolved,
                            "reason": attachment.reason,
                        }
                        for attachment in scaffold.operator_attachments
                    ),
                    "local_scope_relations": scaffold.local_scope_relations,
                    "candidate_head_links": scaffold.candidate_head_links,
                    "unresolved_attachments": scaffold.unresolved_attachments,
                    "confidence": scaffold.confidence,
                    "provenance": scaffold.provenance,
                }
                for scaffold in bundle.phrase_scaffolds
            ),
            "operator_carriers": tuple(
                {
                    "operator_id": carrier.operator_id,
                    "operator_kind": carrier.operator_kind.value,
                    "carrier_unit_ids": carrier.carrier_unit_ids,
                    "scope_anchor_refs": carrier.scope_anchor_refs,
                    "scope_uncertain": carrier.scope_uncertain,
                    "confidence": carrier.confidence,
                    "provenance": carrier.provenance,
                }
                for carrier in bundle.operator_carriers
            ),
            "dictum_carriers": tuple(
                {
                    "carrier_id": carrier.carrier_id,
                    "dictum_candidate_id": carrier.dictum_candidate_id,
                    "predicate_ref": carrier.predicate_ref,
                    "argument_slot_refs": carrier.argument_slot_refs,
                    "confidence": carrier.confidence,
                    "provenance": carrier.provenance,
                }
                for carrier in bundle.dictum_carriers
            ),
            "modus_carriers": tuple(
                {
                    "carrier_id": carrier.carrier_id,
                    "dictum_candidate_id": carrier.dictum_candidate_id,
                    "stance_kind": carrier.stance_kind,
                    "evidence_refs": carrier.evidence_refs,
                    "unresolved": carrier.unresolved,
                    "confidence": carrier.confidence,
                    "provenance": carrier.provenance,
                }
                for carrier in bundle.modus_carriers
            ),
            "source_anchors": tuple(
                {
                    "anchor_id": anchor.anchor_id,
                    "anchor_kind": anchor.anchor_kind.value,
                    "span_start": anchor.span_start,
                    "span_end": anchor.span_end,
                    "marker_text": anchor.marker_text,
                    "unresolved": anchor.unresolved,
                    "confidence": anchor.confidence,
                    "provenance": anchor.provenance,
                }
                for anchor in bundle.source_anchors
            ),
            "uncertainty_markers": tuple(
                {
                    "marker_id": marker.marker_id,
                    "uncertainty_kind": marker.uncertainty_kind.value,
                    "related_refs": marker.related_refs,
                    "reason": marker.reason,
                    "confidence": marker.confidence,
                }
                for marker in bundle.uncertainty_markers
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "source_dictum_ref": result.telemetry.source_dictum_ref,
            "source_syntax_ref": result.telemetry.source_syntax_ref,
            "source_surface_ref": result.telemetry.source_surface_ref,
            "source_modus_ref": result.telemetry.source_modus_ref,
            "source_modus_ref_kind": result.telemetry.source_modus_ref_kind,
            "source_modus_lineage_ref": result.telemetry.source_modus_lineage_ref,
            "source_discourse_update_ref": result.telemetry.source_discourse_update_ref,
            "source_discourse_update_ref_kind": result.telemetry.source_discourse_update_ref_kind,
            "source_discourse_update_lineage_ref": result.telemetry.source_discourse_update_lineage_ref,
            "substrate_unit_count": result.telemetry.substrate_unit_count,
            "phrase_scaffold_count": result.telemetry.phrase_scaffold_count,
            "operator_carrier_count": result.telemetry.operator_carrier_count,
            "dictum_carrier_count": result.telemetry.dictum_carrier_count,
            "modus_carrier_count": result.telemetry.modus_carrier_count,
            "source_anchor_count": result.telemetry.source_anchor_count,
            "uncertainty_marker_count": result.telemetry.uncertainty_marker_count,
            "operator_kinds": result.telemetry.operator_kinds,
            "uncertainty_kinds": result.telemetry.uncertainty_kinds,
            "reversible_span_mapping_present": result.telemetry.reversible_span_mapping_present,
            "low_coverage_mode": result.telemetry.low_coverage_mode,
            "low_coverage_reasons": result.telemetry.low_coverage_reasons,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "normative_l05_l06_route_active": result.telemetry.normative_l05_l06_route_active,
            "legacy_surface_cue_fallback_used": result.telemetry.legacy_surface_cue_fallback_used,
            "l06_blocked_update_present": result.telemetry.l06_blocked_update_present,
            "l06_guarded_continue_present": result.telemetry.l06_guarded_continue_present,
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_scaffold_ids": result.telemetry.downstream_gate.accepted_scaffold_ids,
                "rejected_scaffold_ids": result.telemetry.downstream_gate.rejected_scaffold_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }

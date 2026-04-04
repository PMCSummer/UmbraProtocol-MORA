from __future__ import annotations

from substrate.concept_framing.models import (
    ConceptFramingBundle,
    ConceptFramingGateDecision,
    ConceptFramingResult,
    ConceptFramingTelemetry,
)


def build_concept_framing_telemetry(
    *,
    bundle: ConceptFramingBundle,
    source_lineage: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: ConceptFramingGateDecision,
    causal_basis: str,
) -> ConceptFramingTelemetry:
    return ConceptFramingTelemetry(
        source_lineage=source_lineage,
        source_acquisition_ref=bundle.source_acquisition_ref,
        source_perspective_chain_ref=bundle.source_perspective_chain_ref,
        source_applicability_ref=bundle.source_applicability_ref,
        source_runtime_graph_ref=bundle.source_runtime_graph_ref,
        source_grounded_ref=bundle.source_grounded_ref,
        source_dictum_ref=bundle.source_dictum_ref,
        source_syntax_ref=bundle.source_syntax_ref,
        source_surface_ref=bundle.source_surface_ref,
        framing_record_count=len(bundle.framing_records),
        competition_link_count=len(bundle.competition_links),
        frame_families=tuple(dict.fromkeys(record.frame_family.value for record in bundle.framing_records)),
        framing_statuses=tuple(dict.fromkeys(record.framing_status.value for record in bundle.framing_records)),
        vulnerability_levels=tuple(
            dict.fromkeys(record.vulnerability_profile.vulnerability_level.value for record in bundle.framing_records)
        ),
        low_coverage_mode=bundle.low_coverage_mode,
        low_coverage_reasons=bundle.low_coverage_reasons,
        ambiguity_reasons=bundle.ambiguity_reasons,
        l06_update_proposal_not_bound_here=bundle.l06_update_proposal_not_bound_here,
        repair_trigger_basis_incomplete=bundle.repair_trigger_basis_incomplete,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def concept_framing_result_snapshot(result: ConceptFramingResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_final_semantic_closure": result.no_final_semantic_closure,
        "bundle": {
            "source_acquisition_ref": bundle.source_acquisition_ref,
            "source_perspective_chain_ref": bundle.source_perspective_chain_ref,
            "source_applicability_ref": bundle.source_applicability_ref,
            "source_runtime_graph_ref": bundle.source_runtime_graph_ref,
            "source_grounded_ref": bundle.source_grounded_ref,
            "source_dictum_ref": bundle.source_dictum_ref,
            "source_syntax_ref": bundle.source_syntax_ref,
            "source_surface_ref": bundle.source_surface_ref,
            "linked_acquisition_ids": bundle.linked_acquisition_ids,
            "linked_proposition_ids": bundle.linked_proposition_ids,
            "linked_semantic_unit_ids": bundle.linked_semantic_unit_ids,
            "ambiguity_reasons": bundle.ambiguity_reasons,
            "low_coverage_mode": bundle.low_coverage_mode,
            "low_coverage_reasons": bundle.low_coverage_reasons,
            "l06_update_proposal_not_bound_here": bundle.l06_update_proposal_not_bound_here,
            "repair_trigger_basis_incomplete": bundle.repair_trigger_basis_incomplete,
            "no_final_semantic_closure": bundle.no_final_semantic_closure,
            "reason": bundle.reason,
            "framing_records": tuple(
                {
                    "framing_id": record.framing_id,
                    "acquisition_id": record.acquisition_id,
                    "semantic_unit_id": record.semantic_unit_id,
                    "frame_family": record.frame_family.value,
                    "framing_status": record.framing_status.value,
                    "frame_components": record.frame_components,
                    "framing_basis": record.framing_basis,
                    "alternative_framings": tuple(family.value for family in record.alternative_framings),
                    "vulnerability_profile": {
                        "vulnerability_level": record.vulnerability_profile.vulnerability_level.value,
                        "dimensions": record.vulnerability_profile.dimensions,
                        "fragility_reasons": record.vulnerability_profile.fragility_reasons,
                        "high_impact": record.vulnerability_profile.high_impact,
                        "impact_radius": record.vulnerability_profile.impact_radius,
                    },
                    "unresolved_dependencies": record.unresolved_dependencies,
                    "reframing_conditions": tuple(
                        {
                            "condition_id": cond.condition_id,
                            "condition_kind": cond.condition_kind.value,
                            "trigger_reason": cond.trigger_reason,
                            "confidence": cond.confidence,
                            "provenance": cond.provenance,
                        }
                        for cond in record.reframing_conditions
                    ),
                    "downstream_cautions": record.downstream_cautions,
                    "downstream_permissions": record.downstream_permissions,
                    "context_anchor": record.context_anchor,
                    "confidence": record.confidence,
                    "provenance": record.provenance,
                }
                for record in bundle.framing_records
            ),
            "competition_links": tuple(
                {
                    "competition_id": link.competition_id,
                    "member_framing_ids": link.member_framing_ids,
                    "competing_framing_ids": link.competing_framing_ids,
                    "compatible_framing_ids": link.compatible_framing_ids,
                    "confidence": link.confidence,
                    "provenance": link.provenance,
                }
                for link in bundle.competition_links
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "source_acquisition_ref": result.telemetry.source_acquisition_ref,
            "source_perspective_chain_ref": result.telemetry.source_perspective_chain_ref,
            "source_applicability_ref": result.telemetry.source_applicability_ref,
            "source_runtime_graph_ref": result.telemetry.source_runtime_graph_ref,
            "source_grounded_ref": result.telemetry.source_grounded_ref,
            "source_dictum_ref": result.telemetry.source_dictum_ref,
            "source_syntax_ref": result.telemetry.source_syntax_ref,
            "source_surface_ref": result.telemetry.source_surface_ref,
            "framing_record_count": result.telemetry.framing_record_count,
            "competition_link_count": result.telemetry.competition_link_count,
            "frame_families": result.telemetry.frame_families,
            "framing_statuses": result.telemetry.framing_statuses,
            "vulnerability_levels": result.telemetry.vulnerability_levels,
            "low_coverage_mode": result.telemetry.low_coverage_mode,
            "low_coverage_reasons": result.telemetry.low_coverage_reasons,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "l06_update_proposal_not_bound_here": result.telemetry.l06_update_proposal_not_bound_here,
            "repair_trigger_basis_incomplete": result.telemetry.repair_trigger_basis_incomplete,
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_framing_ids": result.telemetry.downstream_gate.accepted_framing_ids,
                "rejected_framing_ids": result.telemetry.downstream_gate.rejected_framing_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }

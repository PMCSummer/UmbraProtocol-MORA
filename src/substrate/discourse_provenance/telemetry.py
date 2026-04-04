from __future__ import annotations

from substrate.discourse_provenance.models import (
    PerspectiveChainBundle,
    PerspectiveChainGateDecision,
    PerspectiveChainResult,
    PerspectiveChainTelemetry,
)


def build_perspective_chain_telemetry(
    *,
    bundle: PerspectiveChainBundle,
    source_lineage: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: PerspectiveChainGateDecision,
    causal_basis: str,
) -> PerspectiveChainTelemetry:
    return PerspectiveChainTelemetry(
        source_lineage=source_lineage,
        source_applicability_ref=bundle.source_applicability_ref,
        source_runtime_graph_ref=bundle.source_runtime_graph_ref,
        source_grounded_ref=bundle.source_grounded_ref,
        source_dictum_ref=bundle.source_dictum_ref,
        source_syntax_ref=bundle.source_syntax_ref,
        source_surface_ref=bundle.source_surface_ref,
        chain_record_count=len(bundle.chain_records),
        commitment_lineage_count=len(bundle.commitment_lineages),
        wrapped_proposition_count=len(bundle.wrapped_propositions),
        cross_turn_link_count=len(bundle.cross_turn_links),
        assertion_modes=tuple(dict.fromkeys(record.assertion_mode.value for record in bundle.chain_records)),
        source_classes=tuple(dict.fromkeys(record.source_class.value for record in bundle.chain_records)),
        perspective_owners=tuple(dict.fromkeys(record.perspective_owner.value for record in bundle.chain_records)),
        commitment_owners=tuple(dict.fromkeys(record.commitment_owner.value for record in bundle.chain_records)),
        low_coverage_mode=bundle.low_coverage_mode,
        low_coverage_reasons=bundle.low_coverage_reasons,
        ambiguity_reasons=bundle.ambiguity_reasons,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def perspective_chain_result_snapshot(result: PerspectiveChainResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_truth_upgrade": result.no_truth_upgrade,
        "bundle": {
            "source_applicability_ref": bundle.source_applicability_ref,
            "source_runtime_graph_ref": bundle.source_runtime_graph_ref,
            "source_grounded_ref": bundle.source_grounded_ref,
            "source_dictum_ref": bundle.source_dictum_ref,
            "source_syntax_ref": bundle.source_syntax_ref,
            "source_surface_ref": bundle.source_surface_ref,
            "linked_proposition_ids": bundle.linked_proposition_ids,
            "linked_semantic_unit_ids": bundle.linked_semantic_unit_ids,
            "ambiguity_reasons": bundle.ambiguity_reasons,
            "low_coverage_mode": bundle.low_coverage_mode,
            "low_coverage_reasons": bundle.low_coverage_reasons,
            "no_truth_upgrade": bundle.no_truth_upgrade,
            "reason": bundle.reason,
            "chain_records": tuple(
                {
                    "chain_id": record.chain_id,
                    "proposition_id": record.proposition_id,
                    "semantic_unit_id": record.semantic_unit_id,
                    "discourse_level": record.discourse_level,
                    "current_anchor": record.current_anchor,
                    "provenance_path": record.provenance_path,
                    "perspective_stack": record.perspective_stack,
                    "commitment_owner": record.commitment_owner.value,
                    "perspective_owner": record.perspective_owner.value,
                    "assertion_mode": record.assertion_mode.value,
                    "source_class": record.source_class.value,
                    "confidence": record.confidence,
                    "provenance": record.provenance,
                }
                for record in bundle.chain_records
            ),
            "commitment_lineages": tuple(
                {
                    "lineage_id": lineage.lineage_id,
                    "proposition_id": lineage.proposition_id,
                    "commitment_owner": lineage.commitment_owner.value,
                    "ownership_conflict": lineage.ownership_conflict,
                    "lineage_path": lineage.lineage_path,
                    "downstream_constraints": lineage.downstream_constraints,
                    "confidence": lineage.confidence,
                    "provenance": lineage.provenance,
                }
                for lineage in bundle.commitment_lineages
            ),
            "wrapped_propositions": tuple(
                {
                    "wrapper_id": wrapped.wrapper_id,
                    "proposition_id": wrapped.proposition_id,
                    "semantic_unit_id": wrapped.semantic_unit_id,
                    "commitment_owner": wrapped.commitment_owner.value,
                    "perspective_owner": wrapped.perspective_owner.value,
                    "assertion_mode": wrapped.assertion_mode.value,
                    "source_class": wrapped.source_class.value,
                    "discourse_level": wrapped.discourse_level,
                    "provenance_path": wrapped.provenance_path,
                    "perspective_stack": wrapped.perspective_stack,
                    "downstream_constraints": wrapped.downstream_constraints,
                    "confidence": wrapped.confidence,
                    "provenance": wrapped.provenance,
                }
                for wrapped in bundle.wrapped_propositions
            ),
            "cross_turn_links": tuple(
                {
                    "link_id": link.link_id,
                    "chain_id": link.chain_id,
                    "previous_anchor": link.previous_anchor,
                    "current_anchor": link.current_anchor,
                    "attachment_state": link.attachment_state.value,
                    "repair_reason": link.repair_reason,
                    "confidence": link.confidence,
                    "provenance": link.provenance,
                }
                for link in bundle.cross_turn_links
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "source_applicability_ref": result.telemetry.source_applicability_ref,
            "source_runtime_graph_ref": result.telemetry.source_runtime_graph_ref,
            "source_grounded_ref": result.telemetry.source_grounded_ref,
            "source_dictum_ref": result.telemetry.source_dictum_ref,
            "source_syntax_ref": result.telemetry.source_syntax_ref,
            "source_surface_ref": result.telemetry.source_surface_ref,
            "chain_record_count": result.telemetry.chain_record_count,
            "commitment_lineage_count": result.telemetry.commitment_lineage_count,
            "wrapped_proposition_count": result.telemetry.wrapped_proposition_count,
            "cross_turn_link_count": result.telemetry.cross_turn_link_count,
            "assertion_modes": result.telemetry.assertion_modes,
            "source_classes": result.telemetry.source_classes,
            "perspective_owners": result.telemetry.perspective_owners,
            "commitment_owners": result.telemetry.commitment_owners,
            "low_coverage_mode": result.telemetry.low_coverage_mode,
            "low_coverage_reasons": result.telemetry.low_coverage_reasons,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_chain_ids": result.telemetry.downstream_gate.accepted_chain_ids,
                "rejected_chain_ids": result.telemetry.downstream_gate.rejected_chain_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }

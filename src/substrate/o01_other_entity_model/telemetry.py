from __future__ import annotations

from substrate.o01_other_entity_model.models import O01OtherEntityModelResult


def o01_other_entity_model_snapshot(
    result: O01OtherEntityModelResult,
) -> dict[str, object]:
    if not isinstance(result, O01OtherEntityModelResult):
        raise TypeError("o01_other_entity_model_snapshot requires O01OtherEntityModelResult")
    return {
        "state": {
            "model_id": result.state.model_id,
            "tick_index": result.state.tick_index,
            "entities": tuple(
                {
                    "entity_id": entity.entity_id,
                    "entity_kind": entity.entity_kind.value,
                    "model_scope": entity.model_scope.value,
                    "identity_confidence": entity.identity_confidence,
                    "stable_claims": entity.stable_claims,
                    "temporary_state_hypotheses": entity.temporary_state_hypotheses,
                    "probable_goals": entity.probable_goals,
                    "knowledge_boundary_estimates": entity.knowledge_boundary_estimates,
                    "attention_targets": entity.attention_targets,
                    "trust_or_reliability_markers": entity.trust_or_reliability_markers,
                    "uncertainty_map": entity.uncertainty_map,
                    "interaction_history_links": entity.interaction_history_links,
                    "revision_history": tuple(
                        {
                            "event_kind": event.event_kind.value,
                            "field_name": event.field_name,
                            "detail": event.detail,
                            "provenance": event.provenance,
                        }
                        for event in entity.revision_history
                    ),
                    "belief_overlay": {
                        "belief_candidates": entity.belief_overlay.belief_candidates,
                        "ignorance_candidates": entity.belief_overlay.ignorance_candidates,
                        "belief_attribution_uncertainty": entity.belief_overlay.belief_attribution_uncertainty,
                        "evidence_basis": entity.belief_overlay.evidence_basis,
                        "revision_triggers": entity.belief_overlay.revision_triggers,
                    },
                    "provenance": entity.provenance,
                }
                for entity in result.state.entities
            ),
            "current_user_entity_id": result.state.current_user_entity_id,
            "referenced_other_entity_ids": result.state.referenced_other_entity_ids,
            "third_party_entity_ids": result.state.third_party_entity_ids,
            "minimal_other_entity_ids": result.state.minimal_other_entity_ids,
            "competing_entity_models": result.state.competing_entity_models,
            "entity_not_individuated": result.state.entity_not_individuated,
            "perspective_underconstrained": result.state.perspective_underconstrained,
            "no_safe_state_claim": result.state.no_safe_state_claim,
            "temporary_only_not_stable": result.state.temporary_only_not_stable,
            "knowledge_boundary_unknown": result.state.knowledge_boundary_unknown,
            "contradiction_count": result.state.contradiction_count,
            "projection_guard_triggered": result.state.projection_guard_triggered,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "current_user_model_ready": result.gate.current_user_model_ready,
            "entity_individuation_ready": result.gate.entity_individuation_ready,
            "clarification_ready": result.gate.clarification_ready,
            "downstream_consumer_ready": result.gate.downstream_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "o01_first_slice_only": result.scope_marker.o01_first_slice_only,
            "o02_o03_not_implemented": result.scope_marker.o02_o03_not_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "model_id": result.telemetry.model_id,
            "tick_index": result.telemetry.tick_index,
            "entity_count": result.telemetry.entity_count,
            "current_user_model_ready": result.telemetry.current_user_model_ready,
            "third_party_models_active": result.telemetry.third_party_models_active,
            "stable_claim_count": result.telemetry.stable_claim_count,
            "temporary_hypothesis_count": result.telemetry.temporary_hypothesis_count,
            "contradiction_count": result.telemetry.contradiction_count,
            "knowledge_boundary_known_count": result.telemetry.knowledge_boundary_known_count,
            "projection_guard_triggered": result.telemetry.projection_guard_triggered,
            "no_safe_state_claim": result.telemetry.no_safe_state_claim,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "attribution_status": result.attribution_status.value,
        "reason": result.reason,
    }

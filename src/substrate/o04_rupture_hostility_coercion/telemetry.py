from __future__ import annotations

from substrate.o04_rupture_hostility_coercion.models import O04DynamicResult


def o04_rupture_hostility_coercion_snapshot(
    result: O04DynamicResult,
) -> dict[str, object]:
    if not isinstance(result, O04DynamicResult):
        raise TypeError("o04_rupture_hostility_coercion_snapshot requires O04DynamicResult")
    return {
        "state": {
            "interaction_model_id": result.state.interaction_model_id,
            "agent_refs": result.state.agent_refs,
            "directional_links": tuple(_link_snapshot(link) for link in result.state.directional_links),
            "rupture_status": result.state.rupture_status.value,
            "hostility_candidates": result.state.hostility_candidates,
            "coercion_candidates": result.state.coercion_candidates,
            "retaliation_candidates": result.state.retaliation_candidates,
            "counterevidence_summary": result.state.counterevidence_summary,
            "uncertainty_markers": result.state.uncertainty_markers,
            "no_safe_dynamic_claim": result.state.no_safe_dynamic_claim,
            "dependency_model_underconstrained": result.state.dependency_model_underconstrained,
            "tone_shortcut_forbidden_applied": result.state.tone_shortcut_forbidden_applied,
            "legitimacy_boundary_underconstrained": (
                result.state.legitimacy_boundary_underconstrained
            ),
            "justification_links": result.state.justification_links,
            "provenance": result.state.provenance,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "dynamic_contract_consumer_ready": result.gate.dynamic_contract_consumer_ready,
            "directionality_consumer_ready": result.gate.directionality_consumer_ready,
            "protective_handoff_consumer_ready": result.gate.protective_handoff_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "o04_first_slice_only": result.scope_marker.o04_first_slice_only,
            "r05_not_implemented": result.scope_marker.r05_not_implemented,
            "v_line_not_implemented": result.scope_marker.v_line_not_implemented,
            "p04_not_implemented": result.scope_marker.p04_not_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "interaction_model_id": result.telemetry.interaction_model_id,
            "tick_index": result.telemetry.tick_index,
            "dynamic_type": result.telemetry.dynamic_type.value,
            "rupture_status": result.telemetry.rupture_status.value,
            "severity_band": result.telemetry.severity_band.value,
            "certainty_band": result.telemetry.certainty_band.value,
            "directionality_kind": result.telemetry.directionality_kind.value,
            "leverage_surface": result.telemetry.leverage_surface.value,
            "legitimacy_hint_status": result.telemetry.legitimacy_hint_status.value,
            "coercion_candidate_count": result.telemetry.coercion_candidate_count,
            "hostility_candidate_count": result.telemetry.hostility_candidate_count,
            "no_safe_dynamic_claim": result.telemetry.no_safe_dynamic_claim,
            "dependency_model_underconstrained": (
                result.telemetry.dependency_model_underconstrained
            ),
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }


def _link_snapshot(link: object) -> dict[str, object]:
    return {
        "link_id": getattr(link, "link_id"),
        "actor_ref": getattr(link, "actor_ref"),
        "target_ref": getattr(link, "target_ref"),
        "dynamic_type": getattr(link, "dynamic_type").value,
        "leverage_surface": getattr(link, "leverage_surface").value,
        "blocked_option_ref": getattr(link, "blocked_option_ref"),
        "threatened_outcome_ref": getattr(link, "threatened_outcome_ref"),
        "directionality_kind": getattr(link, "directionality_kind").value,
        "legitimacy_hint_status": getattr(link, "legitimacy_hint_status").value,
        "severity_band": getattr(link, "severity_band").value,
        "certainty_band": getattr(link, "certainty_band").value,
        "evidence_refs": getattr(link, "evidence_refs"),
        "counterevidence_refs": getattr(link, "counterevidence_refs"),
        "temporal_scope": getattr(link, "temporal_scope"),
        "status": getattr(link, "status"),
        "provenance": getattr(link, "provenance"),
    }

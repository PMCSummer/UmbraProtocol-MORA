from __future__ import annotations

from substrate.t03_hypothesis_competition.models import T03CompetitionResult


def t03_hypothesis_competition_snapshot(result: T03CompetitionResult) -> dict[str, object]:
    if not isinstance(result, T03CompetitionResult):
        raise TypeError("t03_hypothesis_competition_snapshot requires T03CompetitionResult")
    return {
        "state": {
            "competition_id": result.state.competition_id,
            "source_t01_scene_id": result.state.source_t01_scene_id,
            "source_t02_constrained_scene_id": result.state.source_t02_constrained_scene_id,
            "candidates": tuple(
                {
                    "hypothesis_id": item.hypothesis_id,
                    "scene_variant_id": item.scene_variant_id,
                    "support_sources": item.support_sources,
                    "violated_constraints": item.violated_constraints,
                    "satisfied_constraints": item.satisfied_constraints,
                    "unresolved_load": item.unresolved_load,
                    "authority_profile": item.authority_profile,
                    "competition_score": item.competition_score,
                    "stability_state": item.stability_state.value,
                    "divergence_signature": item.divergence_signature,
                    "status": item.status.value,
                    "provenance": item.provenance,
                }
                for item in result.state.candidates
            ),
            "convergence_status": result.state.convergence_status.value,
            "current_leader_hypothesis_id": result.state.current_leader_hypothesis_id,
            "provisional_frontrunner_hypothesis_id": (
                result.state.provisional_frontrunner_hypothesis_id
            ),
            "tied_competitor_ids": result.state.tied_competitor_ids,
            "blocked_hypothesis_ids": result.state.blocked_hypothesis_ids,
            "eliminated_hypothesis_ids": result.state.eliminated_hypothesis_ids,
            "reactivated_hypothesis_ids": result.state.reactivated_hypothesis_ids,
            "honest_nonconvergence": result.state.honest_nonconvergence,
            "bounded_plurality": result.state.bounded_plurality,
            "publication_frontier": {
                "current_leader": result.state.publication_frontier.current_leader,
                "competitive_neighborhood": (
                    result.state.publication_frontier.competitive_neighborhood
                ),
                "unresolved_conflicts": result.state.publication_frontier.unresolved_conflicts,
                "open_slots": result.state.publication_frontier.open_slots,
                "authority_profile": result.state.publication_frontier.authority_profile,
                "stability_status": result.state.publication_frontier.stability_status,
                "provenance": result.state.publication_frontier.provenance,
            },
            "operations_applied": result.state.operations_applied,
            "source_authority_tags": result.state.source_authority_tags,
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "convergence_consumer_ready": result.gate.convergence_consumer_ready,
            "frontier_consumer_ready": result.gate.frontier_consumer_ready,
            "nonconvergence_preserved": result.gate.nonconvergence_preserved,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "t03_first_slice_only": result.scope_marker.t03_first_slice_only,
            "t04_implemented": result.scope_marker.t04_implemented,
            "o01_implemented": result.scope_marker.o01_implemented,
            "o02_implemented": result.scope_marker.o02_implemented,
            "o03_implemented": result.scope_marker.o03_implemented,
            "full_silent_thought_line_implemented": (
                result.scope_marker.full_silent_thought_line_implemented
            ),
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "competition_id": result.telemetry.competition_id,
            "source_t01_scene_id": result.telemetry.source_t01_scene_id,
            "source_t02_constrained_scene_id": result.telemetry.source_t02_constrained_scene_id,
            "convergence_status": result.telemetry.convergence_status.value,
            "candidates_count": result.telemetry.candidates_count,
            "blocked_hypothesis_count": result.telemetry.blocked_hypothesis_count,
            "eliminated_hypothesis_count": result.telemetry.eliminated_hypothesis_count,
            "reactivated_hypothesis_count": result.telemetry.reactivated_hypothesis_count,
            "tied_competitor_count": result.telemetry.tied_competitor_count,
            "bounded_plurality": result.telemetry.bounded_plurality,
            "honest_nonconvergence": result.telemetry.honest_nonconvergence,
            "convergence_consumer_ready": result.telemetry.convergence_consumer_ready,
            "frontier_consumer_ready": result.telemetry.frontier_consumer_ready,
            "nonconvergence_preserved": result.telemetry.nonconvergence_preserved,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }

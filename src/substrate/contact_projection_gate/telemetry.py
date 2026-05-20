from __future__ import annotations

from dataclasses import asdict

from .models import ProjectedSubjectTickInputs


def contact_projection_snapshot(result: ProjectedSubjectTickInputs) -> dict[str, object]:
    return {
        "projection_id": result.projection_id,
        "source_contact_frame_ref": result.source_contact_frame_ref,
        "projection_status": result.projection_status,
        "public_basis_refs": result.public_basis_refs,
        "blocked_projection_reasons": result.blocked_projection_reasons,
        "ab_counts": {
            "public_observation_refs": len(result.projected_ab_input.public_observation_refs),
            "public_effect_refs": len(result.projected_ab_input.public_effect_refs),
            "passive_public_event_refs": len(result.projected_ab_input.passive_public_event_refs),
        },
        "acp01_basis_counts": {
            "action_surface_basis_refs": len(result.projected_acp01_basis.action_surface_basis_refs),
            "knowledge_hint_refs": len(result.projected_acp01_basis.knowledge_hint_refs),
            "language_hint_refs": len(result.projected_acp01_basis.language_hint_refs),
            "sensory_candidate_refs": len(result.projected_acp01_basis.sensory_candidate_refs),
        },
        "ap01_lineage_counts": {
            "request_refs": len(result.projected_ap01_lineage.request_refs),
            "effect_refs": len(result.projected_ap01_lineage.effect_refs),
            "correlation_refs": len(result.projected_ap01_lineage.correlation_refs),
        },
        "authority_flags": asdict(result.authority_flags),
        "counters": asdict(result.counters),
        "action_request_emitted": result.action_request_emitted,
        "world_submission_emitted": result.world_submission_emitted,
        "fact_claimed": result.fact_claimed,
        "cause_confirmed": result.cause_confirmed,
        "value_assigned": result.value_assigned,
        "mature_recipe_claimed": result.mature_recipe_claimed,
        "mature_skill_claimed": result.mature_skill_claimed,
        "automation_claimed": result.automation_claimed,
    }


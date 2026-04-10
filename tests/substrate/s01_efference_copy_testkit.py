from __future__ import annotations

from substrate.s01_efference_copy import (
    S01EfferenceCopyState,
    build_s01_efference_copy,
)


def build_s01(
    *,
    case_id: str,
    tick_index: int,
    c04_selected_mode: str = "continue_stream",
    c04_execution_mode_claim: str | None = None,
    c05_validity_action: str = "allow_reuse",
    c05_no_safe_reuse: bool = False,
    c05_revalidation_required: bool = False,
    c05_dependency_contaminated: bool = False,
    world_grounded_transition_admissible: bool = True,
    world_effect_feedback_correlated: bool = False,
    world_confidence: float | None = 0.5,
    world_incomplete: bool = False,
    world_degraded: bool = False,
    emit_world_action_candidate: bool = False,
    prior_selected_mode: str | None = None,
    prior_state: S01EfferenceCopyState | None = None,
    register_prediction: bool = True,
):
    return build_s01_efference_copy(
        tick_id=f"s01-{case_id}-{tick_index}",
        tick_index=tick_index,
        c04_selected_mode=c04_selected_mode,
        c04_execution_mode_claim=c04_execution_mode_claim or c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_no_safe_reuse=c05_no_safe_reuse,
        c05_revalidation_required=c05_revalidation_required,
        c05_dependency_contaminated=c05_dependency_contaminated,
        world_grounded_transition_admissible=world_grounded_transition_admissible,
        world_effect_feedback_correlated=world_effect_feedback_correlated,
        world_confidence=world_confidence,
        world_incomplete=world_incomplete,
        world_degraded=world_degraded,
        emit_world_action_candidate=emit_world_action_candidate,
        prior_selected_mode=prior_selected_mode,
        prior_state=prior_state,
        source_lineage=(f"test:{case_id}",),
        register_prediction=register_prediction,
    )

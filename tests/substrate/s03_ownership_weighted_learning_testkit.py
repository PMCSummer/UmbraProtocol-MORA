from __future__ import annotations

from substrate.s03_ownership_weighted_learning import (
    S03OwnershipWeightedLearningState,
    build_s03_ownership_weighted_learning,
)
from tests.substrate.s01_efference_copy_testkit import build_s01
from tests.substrate.s02_prediction_boundary_testkit import build_s02


def build_s03(
    *,
    case_id: str,
    tick_index: int,
    s01_result=None,
    s02_result=None,
    c04_selected_mode: str = "continue_stream",
    c05_validity_action: str = "allow_reuse",
    c05_revalidation_required: bool = False,
    c05_dependency_contaminated: bool = False,
    c05_no_safe_reuse: bool = False,
    context_shift_detected: bool = False,
    prior_state: S03OwnershipWeightedLearningState | None = None,
    ownership_weighting_enabled: bool = True,
    repeated_evidence_enabled: bool = True,
):
    s01_result = s01_result or build_s01(
        case_id=f"{case_id}-s01",
        tick_index=max(1, tick_index - 1),
        c04_selected_mode=c04_selected_mode,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    s02_result = s02_result or build_s02(
        case_id=f"{case_id}-s02",
        tick_index=tick_index,
        s01_result=s01_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=c05_revalidation_required,
        c05_dependency_contaminated=c05_dependency_contaminated,
        context_shift_detected=context_shift_detected,
        effector_available=True,
    )
    return build_s03_ownership_weighted_learning(
        tick_id=f"s03-{case_id}-{tick_index}",
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=c05_revalidation_required,
        c05_dependency_contaminated=c05_dependency_contaminated,
        c05_no_safe_reuse=c05_no_safe_reuse,
        context_shift_detected=context_shift_detected,
        prior_state=prior_state,
        source_lineage=(f"test:{case_id}",),
        ownership_weighting_enabled=ownership_weighting_enabled,
        repeated_evidence_enabled=repeated_evidence_enabled,
    )

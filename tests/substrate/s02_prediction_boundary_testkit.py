from __future__ import annotations

from substrate.s02_prediction_boundary import (
    S02PredictionBoundaryState,
    build_s02_prediction_boundary,
)
from substrate.s01_efference_copy import S01EfferenceCopyResult


def build_s02(
    *,
    case_id: str,
    tick_index: int,
    s01_result: S01EfferenceCopyResult,
    c04_selected_mode: str = "continue_stream",
    c05_validity_action: str = "allow_reuse",
    c05_revalidation_required: bool = False,
    c05_dependency_contaminated: bool = False,
    context_shift_detected: bool = False,
    effector_available: bool = True,
    observation_degraded: bool = False,
    prior_state: S02PredictionBoundaryState | None = None,
    aggregation_enabled: bool = True,
    controllability_sensitive_signal_enabled: bool = True,
    manual_channel_map: dict[str, str] | None = None,
):
    return build_s02_prediction_boundary(
        tick_id=f"s02-{case_id}-{tick_index}",
        tick_index=tick_index,
        s01_result=s01_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=c05_revalidation_required,
        c05_dependency_contaminated=c05_dependency_contaminated,
        context_shift_detected=context_shift_detected,
        effector_available=effector_available,
        observation_degraded=observation_degraded,
        prior_state=prior_state,
        source_lineage=(f"test:{case_id}",),
        context_scope=("test", case_id),
        aggregation_enabled=aggregation_enabled,
        controllability_sensitive_signal_enabled=controllability_sensitive_signal_enabled,
        manual_channel_map=manual_channel_map,
    )

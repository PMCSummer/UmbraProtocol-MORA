from __future__ import annotations

from dataclasses import dataclass

from substrate.s04_interoceptive_self_binding import (
    S04CandidateClass,
    S04CandidateSignal,
    S04InteroceptiveSelfBindingState,
    build_s04_interoceptive_self_binding,
)
from tests.substrate.s01_efference_copy_testkit import build_s01
from tests.substrate.s02_prediction_boundary_testkit import build_s02
from tests.substrate.s03_ownership_weighted_learning_testkit import build_s03


@dataclass(frozen=True, slots=True)
class S04HarnessConfig:
    case_id: str
    tick_index: int
    regulatory_support: float = 0.65
    continuity_support: float = 0.62
    boundary_support: float = 0.62
    ownership_support: float = 0.62
    coupling_support: float = 0.55
    temporal_validity: float = 0.75
    contamination: float = 0.1
    include_mixed_channel: bool = True
    include_generic_channel: bool = True
    include_transient_channel: bool = True
    c05_revalidation_required: bool = False
    context_shift_detected: bool = False


def build_s04(
    *,
    case_id: str,
    tick_index: int,
    s01_result=None,
    s02_result=None,
    s03_result=None,
    regulation_pressure_level: float = 66.0,
    regulation_dominant_axis: str = "energy",
    c05_revalidation_required: bool = False,
    context_shift_detected: bool = False,
    candidate_signals: tuple[S04CandidateSignal, ...] = (),
    observed_internal_channels: tuple[str, ...] = (),
    prior_state: S04InteroceptiveSelfBindingState | None = None,
    binding_enabled: bool = True,
):
    s01_result = s01_result or build_s01(
        case_id=f"{case_id}-s01",
        tick_index=max(1, tick_index - 2),
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    s02_result = s02_result or build_s02(
        case_id=f"{case_id}-s02",
        tick_index=max(1, tick_index - 1),
        s01_result=s01_result,
        effector_available=True,
    )
    s03_result = s03_result or build_s03(
        case_id=f"{case_id}-s03",
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
    )
    return build_s04_interoceptive_self_binding(
        tick_id=f"s04-{case_id}-{tick_index}",
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        regulation_pressure_level=regulation_pressure_level,
        regulation_dominant_axis=regulation_dominant_axis,
        c05_revalidation_required=c05_revalidation_required,
        context_shift_detected=context_shift_detected,
        candidate_signals=candidate_signals,
        observed_internal_channels=observed_internal_channels,
        prior_state=prior_state,
        source_lineage=(f"test:{case_id}",),
        binding_enabled=binding_enabled,
    )


def build_s04_harness_case(config: S04HarnessConfig):
    candidate_signals = [
        S04CandidateSignal(
            channel_id=f"{config.case_id}:core_regulatory",
            candidate_class=S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
            regulatory_support_hint=config.regulatory_support,
            continuity_support_hint=config.continuity_support,
            boundary_support_hint=config.boundary_support,
            ownership_support_hint=config.ownership_support,
            coupling_support_hint=config.coupling_support,
            temporal_validity_hint=config.temporal_validity,
            contamination_hint=config.contamination,
            source_authority="harness",
            provenance="harness.core_regulatory",
        )
    ]
    if config.include_mixed_channel:
        candidate_signals.append(
            S04CandidateSignal(
                channel_id=f"{config.case_id}:mixed_signal",
                candidate_class=S04CandidateClass.MIXED_INTERNAL_EXTERNAL,
                regulatory_support_hint=max(0.2, config.regulatory_support * 0.6),
                continuity_support_hint=max(0.2, config.continuity_support * 0.5),
                boundary_support_hint=max(0.25, config.boundary_support * 0.6),
                ownership_support_hint=max(0.2, config.ownership_support * 0.6),
                coupling_support_hint=max(0.2, config.coupling_support * 0.5),
                temporal_validity_hint=max(0.3, config.temporal_validity * 0.8),
                contamination_hint=max(config.contamination, 0.3),
                source_authority="harness",
                provenance="harness.mixed",
            )
        )
    observed_channels: list[str] = []
    if config.include_generic_channel:
        observed_channels.append("bookkeeping:internal_cache_counter")
    if config.include_transient_channel:
        observed_channels.append("transient:mode_temp_marker")

    return build_s04(
        case_id=config.case_id,
        tick_index=config.tick_index,
        regulation_pressure_level=max(0.0, min(100.0, config.regulatory_support * 100.0)),
        c05_revalidation_required=config.c05_revalidation_required,
        context_shift_detected=config.context_shift_detected,
        candidate_signals=tuple(candidate_signals),
        observed_internal_channels=tuple(observed_channels),
    )

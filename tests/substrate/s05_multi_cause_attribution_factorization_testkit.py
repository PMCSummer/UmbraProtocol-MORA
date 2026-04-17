from __future__ import annotations

from dataclasses import dataclass

from substrate.s04_interoceptive_self_binding import (
    S04CandidateClass,
    S04CandidateSignal,
)
from substrate.s05_multi_cause_attribution_factorization import (
    S05MultiCauseAttributionState,
    S05OutcomePacketInput,
    build_s05_multi_cause_attribution_factorization,
)
from tests.substrate.s01_efference_copy_testkit import build_s01
from tests.substrate.s02_prediction_boundary_testkit import build_s02
from tests.substrate.s03_ownership_weighted_learning_testkit import build_s03
from tests.substrate.s04_interoceptive_self_binding_testkit import build_s04


@dataclass(frozen=True, slots=True)
class S05HarnessConfig:
    case_id: str
    tick_index: int
    deliberate_internal_act: bool = True
    endogenous_mode_shift: bool = False
    interoceptive_support: float = 0.72
    world_perturbation: bool = False
    observation_noise: float = 0.12
    latent_unmodeled_disturbance: float = 0.0
    c05_revalidation_required: bool = False
    context_shift_detected: bool = False
    world_presence_mode: str | None = None
    late_evidence_tokens: tuple[str, ...] = ()
    factorization_enabled: bool = True


def build_s05(
    *,
    case_id: str,
    tick_index: int,
    s01_result=None,
    s02_result=None,
    s03_result=None,
    s04_result=None,
    c04_selected_mode: str = "continue_stream",
    c05_validity_action: str = "allow_reuse",
    c05_revalidation_required: bool = False,
    world_presence_mode: str = "present",
    world_effect_feedback_correlated: bool = True,
    context_shift_detected: bool = False,
    late_evidence_tokens: tuple[str, ...] = (),
    outcome_packet: S05OutcomePacketInput | None = None,
    prior_state: S05MultiCauseAttributionState | None = None,
    factorization_enabled: bool = True,
):
    s01_result = s01_result or build_s01(
        case_id=f"{case_id}-s01",
        tick_index=max(1, tick_index - 3),
        c04_selected_mode=c04_selected_mode,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=world_effect_feedback_correlated,
        c05_revalidation_required=c05_revalidation_required,
        c05_dependency_contaminated=False,
    )
    s02_result = s02_result or build_s02(
        case_id=f"{case_id}-s02",
        tick_index=max(1, tick_index - 2),
        s01_result=s01_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=c05_revalidation_required,
        c05_dependency_contaminated=False,
        context_shift_detected=context_shift_detected,
        observation_degraded=False,
        effector_available=True,
    )
    s03_result = s03_result or build_s03(
        case_id=f"{case_id}-s03",
        tick_index=max(1, tick_index - 1),
        s01_result=s01_result,
        s02_result=s02_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=c05_revalidation_required,
        c05_dependency_contaminated=False,
        context_shift_detected=context_shift_detected,
    )
    s04_result = s04_result or build_s04(
        case_id=f"{case_id}-s04",
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        c05_revalidation_required=c05_revalidation_required,
        context_shift_detected=context_shift_detected,
    )
    return build_s05_multi_cause_attribution_factorization(
        tick_id=f"s05-{case_id}-{tick_index}",
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        s04_result=s04_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=c05_revalidation_required,
        world_presence_mode=world_presence_mode,
        world_effect_feedback_correlated=world_effect_feedback_correlated,
        context_shift_detected=context_shift_detected,
        late_evidence_tokens=late_evidence_tokens,
        outcome_packet=outcome_packet,
        prior_state=prior_state,
        source_lineage=(f"test:{case_id}",),
        factorization_enabled=factorization_enabled,
    )


def build_s05_harness_case(
    config: S05HarnessConfig,
    *,
    prior_state: S05MultiCauseAttributionState | None = None,
):
    c04_selected_mode = (
        "hold_safe_idle" if config.endogenous_mode_shift else "continue_stream"
    )
    c05_validity_action = (
        "run_selective_revalidation"
        if config.c05_revalidation_required
        else "allow_reuse"
    )
    observation_degraded = config.observation_noise >= 0.55
    dependency_contaminated = config.observation_noise >= 0.45

    s01_result = build_s01(
        case_id=f"{config.case_id}-s01",
        tick_index=max(1, config.tick_index - 3),
        c04_selected_mode=c04_selected_mode,
        emit_world_action_candidate=config.deliberate_internal_act,
        world_effect_feedback_correlated=(
            config.world_perturbation and config.observation_noise < 0.7
        ),
        c05_revalidation_required=config.c05_revalidation_required,
        c05_dependency_contaminated=dependency_contaminated,
    )
    s02_result = build_s02(
        case_id=f"{config.case_id}-s02",
        tick_index=max(1, config.tick_index - 2),
        s01_result=s01_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=config.c05_revalidation_required,
        c05_dependency_contaminated=dependency_contaminated,
        context_shift_detected=(
            config.context_shift_detected or config.endogenous_mode_shift
        ),
        observation_degraded=observation_degraded,
        effector_available=config.deliberate_internal_act,
    )
    s03_result = build_s03(
        case_id=f"{config.case_id}-s03",
        tick_index=max(1, config.tick_index - 1),
        s01_result=s01_result,
        s02_result=s02_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=config.c05_revalidation_required,
        c05_dependency_contaminated=dependency_contaminated,
        context_shift_detected=(
            config.context_shift_detected or config.endogenous_mode_shift
        ),
    )
    intero = max(0.0, min(1.0, config.interoceptive_support))
    candidate_signals = (
        S04CandidateSignal(
            channel_id=f"{config.case_id}:intero_core",
            candidate_class=S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
            regulatory_support_hint=intero,
            continuity_support_hint=max(0.05, intero - 0.08),
            boundary_support_hint=max(0.05, intero - 0.12),
            ownership_support_hint=max(0.05, intero - 0.1),
            coupling_support_hint=max(0.05, intero - 0.1),
            temporal_validity_hint=(
                0.42 if config.c05_revalidation_required else max(0.1, intero - 0.04)
            ),
            contamination_hint=max(0.0, min(1.0, config.observation_noise)),
            source_authority="s04.authorized:s05_harness",
            provenance="s05_harness.intero_core",
        ),
    )
    s04_result = build_s04(
        case_id=f"{config.case_id}-s04",
        tick_index=config.tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        c05_revalidation_required=config.c05_revalidation_required,
        context_shift_detected=(
            config.context_shift_detected or config.endogenous_mode_shift
        ),
        candidate_signals=candidate_signals,
        observed_internal_channels=(
            "bookkeeping:cache_counter",
            "transient:mode_temp_marker",
        ),
        prior_state=None,
    )

    outcome_packet = None
    if config.latent_unmodeled_disturbance > 0.0:
        latent = max(0.0, min(1.0, config.latent_unmodeled_disturbance))
        outcome_packet = S05OutcomePacketInput(
            outcome_packet_id=f"s05-outcome-override:{config.case_id}:{config.tick_index}",
            mismatch_magnitude=max(0.25, latent),
            observed_delta_class="unexpected_change",
            expected_delta_class="weak_prediction_basis",
            outcome_channel="test.s05.latent_disturbance",
            observed_tick=config.tick_index,
            preferred_tick=config.tick_index,
            expires_tick=config.tick_index + 1,
            contaminated=config.observation_noise >= 0.6,
            source_ref="tests.s05_harness.latent_disturbance_override",
        )

    return build_s05(
        case_id=config.case_id,
        tick_index=config.tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        s04_result=s04_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=config.c05_revalidation_required,
        world_presence_mode=(
            config.world_presence_mode
            if config.world_presence_mode is not None
            else ("present" if config.world_perturbation else "absent")
        ),
        world_effect_feedback_correlated=(
            config.world_perturbation and config.observation_noise < 0.7
        ),
        context_shift_detected=(
            config.context_shift_detected or config.endogenous_mode_shift
        ),
        late_evidence_tokens=config.late_evidence_tokens,
        outcome_packet=outcome_packet,
        prior_state=prior_state,
        factorization_enabled=config.factorization_enabled,
    )

from __future__ import annotations

import pytest

from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    dispatch_runtime_tick,
    require_lawful_production_dispatch,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome, execute_subject_tick
from substrate.world_adapter import (
    WorldAdapterInput,
    derive_world_adapter_contract_view,
    WorldEffectStatus,
    WorldLinkStatus,
    build_world_effect_packet,
    build_world_observation_packet,
    run_world_adapter_cycle,
)


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _observation(case_id: str):
    return build_world_observation_packet(
        observation_id=f"obs-{case_id}",
        source_ref="world.sensor.stub",
        observed_at="2026-04-08T20:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def test_world_adapter_generation_observation_action_effect_surfaces() -> None:
    obs = _observation("wa-generation")
    result = run_world_adapter_cycle(
        tick_id="tick-wa-generation",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=obs,
            source_lineage=("test.world",),
        ),
        request_action_candidate=True,
        source_lineage=("test.tick",),
    )
    assert result.state.last_observation_packet is not None
    assert result.state.last_action_packet is not None
    assert result.state.world_link_status == WorldLinkStatus.ACTION_PENDING_EFFECT
    assert result.state.effect_status == WorldEffectStatus.PENDING_FEEDBACK
    assert result.gate.world_grounded_transition_allowed is True
    assert result.gate.externally_effected_change_claim_allowed is False
    contract = derive_world_adapter_contract_view(result)
    assert contract.effect_feedback_correlated is False


def test_world_adapter_unavailable_state_is_first_class() -> None:
    result = run_world_adapter_cycle(
        tick_id="tick-wa-unavailable",
        execution_mode="continue_stream",
    )
    assert result.state.adapter_presence is False
    assert result.state.world_link_status == WorldLinkStatus.UNAVAILABLE
    assert result.state.effect_status == WorldEffectStatus.UNAVAILABLE
    assert result.gate.world_grounded_transition_allowed is False
    assert "world_adapter_absent" in result.gate.restrictions


def test_world_effect_claim_without_feedback_is_blocked() -> None:
    obs = _observation("wa-no-effect")
    result = run_world_adapter_cycle(
        tick_id="tick-wa-no-effect",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=obs,
        ),
        request_action_candidate=True,
    )
    assert result.gate.externally_effected_change_claim_allowed is False
    assert "action_emitted_without_effect_feedback" in result.gate.restrictions


def test_subject_tick_world_requirement_blocks_transition_without_world_presence() -> None:
    no_world = execute_subject_tick(
        _tick_input("wa-rt01-no-world"),
        context=SubjectTickContext(require_world_grounded_transition=True),
    )
    with_world = execute_subject_tick(
        _tick_input("wa-rt01-with-world"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("wa-rt01-with-world"),
            ),
        ),
    )
    assert no_world.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert with_world.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert no_world.state.world_grounded_transition_allowed is False
    assert with_world.state.world_grounded_transition_allowed is True


def test_subject_tick_world_effect_feedback_required_for_externally_effected_claim() -> None:
    without_effect = execute_subject_tick(
        _tick_input("wa-effect-without"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("wa-effect-without"),
            ),
            emit_world_action_candidate=True,
        ),
    )
    with_effect = execute_subject_tick(
        _tick_input("wa-effect-with"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("wa-effect-with"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-wa-effect-with",
                    action_id="world-action-subject-tick-wa-effect-with-1",
                    observed_at="2026-04-08T20:01:00+00:00",
                    source_ref="world.effect.stub",
                    success=True,
                ),
            ),
            emit_world_action_candidate=True,
        ),
    )
    assert without_effect.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert with_effect.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert without_effect.state.world_externally_effected_change_claim_allowed is False
    assert with_effect.state.world_externally_effected_change_claim_allowed is True
    assert without_effect.state.world_effect_feedback_correlated is False
    assert with_effect.state.world_effect_feedback_correlated is True


def test_subject_tick_mismatched_effect_action_id_blocks_strong_claim_and_forces_detour() -> None:
    mismatched = execute_subject_tick(
        _tick_input("wa-effect-mismatch"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("wa-effect-mismatch"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-wa-effect-mismatch",
                    action_id="wrong-action-id",
                    observed_at="2026-04-08T20:01:30+00:00",
                    source_ref="world.effect.stub",
                    success=True,
                ),
            ),
            emit_world_action_candidate=True,
        ),
    )
    assert mismatched.state.world_effect_feedback_correlated is False
    assert mismatched.state.world_externally_effected_change_claim_allowed is False
    assert mismatched.state.world_action_success_claim_allowed is False
    assert mismatched.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_world_adapter_effect_without_action_trace_cannot_grant_strong_success_claim() -> None:
    result = run_world_adapter_cycle(
        tick_id="tick-wa-effect-no-action",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=_observation("wa-effect-no-action"),
            effect_packet=build_world_effect_packet(
                effect_id="eff-wa-effect-no-action",
                action_id="orphan-action",
                observed_at="2026-04-08T20:01:45+00:00",
                source_ref="world.effect.stub",
                success=True,
            ),
        ),
        request_action_candidate=False,
    )
    assert result.state.effect_feedback_correlated is False
    assert result.gate.externally_effected_change_claim_allowed is False
    assert result.gate.world_action_success_claim_allowed is False
    assert "effect_feedback_without_action_trace" in result.gate.restrictions
    assert "effect_feedback_not_correlated_with_action" in result.gate.restrictions


def test_world_seam_ablation_changes_path() -> None:
    enforced = execute_subject_tick(
        _tick_input("wa-ablation-enforced"),
        context=SubjectTickContext(require_world_grounded_transition=True),
    )
    ablated = execute_subject_tick(
        _tick_input("wa-ablation-disabled"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            disable_world_seam_enforcement=True,
        ),
    )
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert ablated.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_world_effect_correlation_ablation_contrast_changes_path() -> None:
    enforced = execute_subject_tick(
        _tick_input("wa-mismatch-ablation-enforced"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("wa-mismatch-ablation-enforced"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-wa-mismatch-ablation-enforced",
                    action_id="wrong-action-id",
                    observed_at="2026-04-08T20:02:00+00:00",
                    source_ref="world.effect.stub",
                    success=True,
                ),
            ),
        ),
    )
    ablated = execute_subject_tick(
        _tick_input("wa-mismatch-ablation-disabled"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            emit_world_action_candidate=True,
            disable_world_seam_enforcement=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("wa-mismatch-ablation-disabled"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-wa-mismatch-ablation-disabled",
                    action_id="wrong-action-id",
                    observed_at="2026-04-08T20:02:15+00:00",
                    source_ref="world.effect.stub",
                    success=True,
                ),
            ),
        ),
    )
    assert enforced.state.world_effect_feedback_correlated is False
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert ablated.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_world_adapter_matrix_available_degraded_unavailable() -> None:
    available = run_world_adapter_cycle(
        tick_id="tick-wa-matrix-available",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=_observation("wa-matrix-available"),
        ),
    )
    degraded = run_world_adapter_cycle(
        tick_id="tick-wa-matrix-degraded",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            adapter_degraded=True,
            observation_packet=_observation("wa-matrix-degraded"),
        ),
        request_action_candidate=True,
    )
    unavailable = run_world_adapter_cycle(
        tick_id="tick-wa-matrix-unavailable",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(adapter_presence=False, adapter_available=False),
    )
    assert available.state.world_link_status == WorldLinkStatus.OBSERVATION_ONLY
    assert degraded.state.world_link_status == WorldLinkStatus.DEGRADED
    assert unavailable.state.world_link_status == WorldLinkStatus.UNAVAILABLE


@pytest.mark.parametrize(
    ("effect_action_id", "require_feedback", "expected_outcome", "expected_claim_allowed"),
    (
        ("world-action-subject-tick-wa-effect-matrix-1", True, SubjectTickOutcome.CONTINUE, True),
        ("wrong-action-id", True, SubjectTickOutcome.REVALIDATE, False),
        ("wrong-action-id", False, SubjectTickOutcome.CONTINUE, False),
    ),
)
def test_world_effect_correlation_matrix(
    effect_action_id: str,
    require_feedback: bool,
    expected_outcome: SubjectTickOutcome,
    expected_claim_allowed: bool,
) -> None:
    result = execute_subject_tick(
        _tick_input("wa-effect-matrix"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=require_feedback,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("wa-effect-matrix"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-wa-effect-matrix",
                    action_id=effect_action_id,
                    observed_at="2026-04-08T20:03:00+00:00",
                    source_ref="world.effect.stub",
                    success=True,
                ),
            ),
        ),
    )
    assert result.state.final_execution_outcome == expected_outcome
    assert result.state.world_externally_effected_change_claim_allowed is expected_claim_allowed


def test_role_boundary_rt01_remains_execution_consumer_not_world_reasoner() -> None:
    result = execute_subject_tick(
        _tick_input("wa-role-boundary"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("wa-role-boundary"),
            ),
        ),
    )
    assert result.state.c04_authority_role == "arbitration"
    assert result.state.c05_authority_role == "invalidation"
    assert result.state.f01_authority_role == "observability_only"
    assert result.no_planner_orchestrator_dependency is True
    assert result.state.world_link_status in {
        WorldLinkStatus.OBSERVATION_ONLY.value,
        WorldLinkStatus.ACTION_PENDING_EFFECT.value,
        WorldLinkStatus.ACTION_EFFECT_OBSERVED.value,
    }


def test_helper_route_world_packets_cannot_masquerade_as_lawful_production() -> None:
    helper = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("wa-helper-route"),
            context=SubjectTickContext(
                require_world_grounded_transition=True,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=True,
                    adapter_available=True,
                    observation_packet=_observation("wa-helper-route"),
                ),
            ),
            route_class=RuntimeRouteClass.HELPER_PATH,
            allow_helper_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert helper.decision.accepted is True
    with pytest.raises(PermissionError):
        require_lawful_production_dispatch(helper)


def test_contour_proof_dispatch_reads_world_seam_as_load_bearing_input() -> None:
    no_world = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("wa-dispatch-no-world"),
            context=SubjectTickContext(require_world_grounded_transition=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    with_world = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("wa-dispatch-with-world"),
            context=SubjectTickContext(
                require_world_grounded_transition=True,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=True,
                    adapter_available=True,
                    observation_packet=_observation("wa-dispatch-with-world"),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert no_world.subject_tick_result is not None
    assert with_world.subject_tick_result is not None
    assert no_world.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert with_world.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE

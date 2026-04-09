from __future__ import annotations

import pytest

from substrate.a_line_normalization import (
    CapabilityStatus,
    build_a_line_normalization,
    derive_a_line_normalization_contract_view,
    a_line_normalization_snapshot,
)
from substrate.self_contour import build_s_minimal_contour
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    derive_subject_tick_contract_view,
    execute_subject_tick,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    dispatch_runtime_tick,
    derive_runtime_dispatch_contract_view,
)
from substrate.world_adapter import (
    WorldAdapterInput,
    build_world_effect_packet,
    build_world_observation_packet,
    run_world_adapter_cycle,
)
from substrate.world_entry_contract import build_world_entry_contract


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
        source_ref="world.sensor.sprint8c",
        observed_at="2026-04-09T18:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def _a_line_contract_result(
    case_id: str,
    *,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c04_mode: str = "continue_stream",
    c05_action: str = "reuse_without_revalidation",
):
    tick_id = f"tick-{case_id}"
    effect_packet = None
    if effect_action_id == "__MATCHED__":
        effect_action_id = f"world-action-{tick_id}"
    if effect_action_id is not None:
        effect_packet = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=effect_action_id,
            observed_at="2026-04-09T18:00:01+00:00",
            source_ref="world.effect.sprint8c",
            success=True,
        )
    adapter_result = run_world_adapter_cycle(
        tick_id=tick_id,
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=include_observation,
            adapter_available=include_observation,
            observation_packet=_observation(case_id) if include_observation else None,
            effect_packet=effect_packet,
        ),
        request_action_candidate=request_action,
        source_lineage=("test.sprint8c.a-line",),
    )
    world_entry_result = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=adapter_result,
        source_lineage=("test.sprint8c.a-line",),
    )
    s_result = build_s_minimal_contour(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        world_adapter_result=adapter_result,
        source_lineage=("test.sprint8c.a-line",),
    )
    a_result = build_a_line_normalization(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_result,
        c04_execution_mode_claim=c04_mode,
        c05_validity_action=c05_action,
        source_lineage=("test.sprint8c.a-line",),
    )
    return a_result


def test_a_line_substrate_materializes_typed_state_and_scope() -> None:
    result = _a_line_contract_result(
        "a-line-typed",
        include_observation=True,
        request_action=True,
        effect_action_id="world-action-tick-a-line-typed",
    )
    view = derive_a_line_normalization_contract_view(result)
    snapshot = a_line_normalization_snapshot(result)
    assert result.state.capability_id.startswith("a-capability:")
    assert result.state.capability_status == CapabilityStatus.AVAILABLE_CAPABILITY
    assert result.gate.available_capability_claim_allowed is True
    assert view.scope == "rt01_contour_only"
    assert view.scope_rt01_contour_only is True
    assert view.scope_a_line_normalization_only is True
    assert view.scope_a04_implemented is False
    assert view.scope_a05_touched is False
    assert view.scope_repo_wide_adoption is False
    assert snapshot["scope_marker"]["a04_implemented"] is False
    assert snapshot["scope_marker"]["a05_touched"] is False


def test_a_line_forbidden_shortcuts_are_machine_readable_without_basis() -> None:
    result = _a_line_contract_result(
        "a-line-no-basis",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    assert result.gate.available_capability_claim_allowed is False
    assert result.gate.no_safe_capability_claim is True
    assert "capability_claim_without_basis" in result.gate.forbidden_shortcuts
    assert "affordance_claim_without_world_or_self_basis" in result.gate.forbidden_shortcuts
    assert result.a04_readiness.admission_ready_for_a04 is False
    assert "a05_untouched_in_this_pass" in result.a04_readiness.restrictions


def test_rt01_a_line_claim_missing_basis_forces_detour() -> None:
    baseline = execute_subject_tick(_tick_input("a-line-rt01-baseline"))
    enforced = execute_subject_tick(
        _tick_input("a-line-rt01-enforced"),
        context=SubjectTickContext(require_a_line_capability_claim=True),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert enforced.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.a_line_normalization_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in enforced.state.execution_checkpoints
    )


def test_rt01_policy_gated_capability_cannot_masquerade_as_free_capability() -> None:
    result = execute_subject_tick(
        _tick_input("a-line-policy-gated"),
        context=SubjectTickContext(
            require_a_line_capability_claim=True,
            dependency_trigger_hits=("trigger:mode_shift",),
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("a-line-policy-gated"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-a-line-policy-gated",
                    action_id="world-action-subject-tick-a-line-policy-gated-1",
                    observed_at="2026-04-09T18:05:01+00:00",
                    source_ref="world.effect.sprint8c",
                    success=True,
                ),
            ),
        ),
    )
    assert result.state.a_policy_conditioned_capability_present is True
    assert "policy_gated_capability_reframed_as_free_action" in result.state.a_forbidden_shortcuts
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_rt01_underconstrained_capability_claim_triggers_revalidation() -> None:
    result = execute_subject_tick(
        _tick_input("a-line-underconstrained"),
        context=SubjectTickContext(
            require_a_line_capability_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("a-line-underconstrained"),
            ),
        ),
    )
    assert result.state.a_underconstrained is True
    assert "underconstrained_capability_presented_as_ready" in result.state.a_forbidden_shortcuts
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_a04_readiness_surface_is_explicit_and_a05_is_untouched() -> None:
    result = _a_line_contract_result(
        "a-line-a04-readiness",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
    )
    assert isinstance(result.a04_readiness.blockers, tuple)
    assert result.a04_readiness.a04_implemented is False
    assert result.a04_readiness.a05_touched is False
    assert result.scope_marker.a04_implemented is False
    assert result.scope_marker.a05_touched is False


def test_a04_readiness_quality_gates_block_weak_or_underconstrained_basis() -> None:
    weak = _a_line_contract_result(
        "a-line-a04-weak",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    underconstrained = _a_line_contract_result(
        "a-line-a04-underconstrained",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
    )
    assert weak.a04_readiness.admission_ready_for_a04 is False
    assert weak.a04_readiness.capability_basis_missing is True
    assert weak.a04_readiness.world_dependency_unmet is True
    assert weak.a04_readiness.self_dependency_unmet is True
    assert weak.a04_readiness.structurally_present_but_not_ready is True
    assert underconstrained.a04_readiness.admission_ready_for_a04 is False
    assert underconstrained.a04_readiness.underconstrained_capability_surface is True
    assert "underconstrained_capability_surface" in underconstrained.a04_readiness.blockers


def test_a04_readiness_can_be_true_for_lawful_basis_without_a04_or_a05_claim() -> None:
    lawful = _a_line_contract_result(
        "a-line-a04-lawful",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    assert lawful.state.capability_status == CapabilityStatus.AVAILABLE_CAPABILITY
    assert lawful.a04_readiness.admission_ready_for_a04 is True
    assert lawful.a04_readiness.structurally_present_but_not_ready is False
    assert lawful.a04_readiness.capability_basis_missing is False
    assert lawful.a04_readiness.world_dependency_unmet is False
    assert lawful.a04_readiness.self_dependency_unmet is False
    assert lawful.a04_readiness.policy_legitimacy_unmet is False
    assert lawful.a04_readiness.underconstrained_capability_surface is False
    assert lawful.a04_readiness.external_means_not_justified is False
    assert lawful.a04_readiness.a04_implemented is False
    assert lawful.a04_readiness.a05_touched is False


def test_a_line_scope_markers_are_consistent_across_contract_surfaces() -> None:
    tick = execute_subject_tick(
        _tick_input("a-line-scope-contract"),
        context=SubjectTickContext(
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("a-line-scope-contract"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-a-line-scope-contract",
                    action_id="world-action-subject-tick-a-line-scope-contract-1",
                    observed_at="2026-04-09T18:12:00+00:00",
                    source_ref="world.effect.sprint8c",
                    success=True,
                ),
            ),
        ),
    )
    dispatch = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("a-line-scope-contract"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    tick_view = derive_subject_tick_contract_view(tick)
    dispatch_view = derive_runtime_dispatch_contract_view(dispatch)
    assert tick_view.a_scope == "rt01_contour_only"
    assert tick_view.a_scope_rt01_contour_only is True
    assert tick_view.a_scope_a_line_normalization_only is True
    assert tick_view.a_scope_readiness_gate_only is True
    assert tick_view.a_scope_a04_implemented is False
    assert tick_view.a_scope_a05_touched is False
    assert tick_view.a_scope_full_agency_stack_implemented is False
    assert tick_view.a_scope_repo_wide_adoption is False
    assert dispatch_view.a_scope == "rt01_contour_only"
    assert dispatch_view.a_scope_readiness_gate_only is True
    assert dispatch_view.a_scope_a04_implemented is False
    assert dispatch_view.a_scope_a05_touched is False
    assert dispatch_view.a_scope_full_agency_stack_implemented is False
    assert dispatch_view.a_scope_repo_wide_adoption is False


def test_rt01_a_line_ablation_contrast_is_causal() -> None:
    enforced = execute_subject_tick(
        _tick_input("a-line-ablation-enforced"),
        context=SubjectTickContext(require_a_line_capability_claim=True),
    )
    ablated = execute_subject_tick(
        _tick_input("a-line-ablation-disabled"),
        context=SubjectTickContext(
            require_a_line_capability_claim=True,
            disable_a_line_enforcement=True,
        ),
    )
    assert enforced.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert ablated.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


@pytest.mark.parametrize(
    ("include_observation", "request_action", "effect_action_id", "expected_status"),
    (
        (True, True, "__MATCHED__", CapabilityStatus.AVAILABLE_CAPABILITY),
        (False, False, None, CapabilityStatus.UNAVAILABLE_CAPABILITY),
        (True, True, None, CapabilityStatus.UNDERCONSTRAINED_CAPABILITY),
    ),
)
def test_a_line_status_matrix_is_typed_and_distinct(
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    expected_status: CapabilityStatus,
) -> None:
    result = _a_line_contract_result(
        f"a-line-matrix-{expected_status.value}",
        include_observation=include_observation,
        request_action=request_action,
        effect_action_id=effect_action_id,
    )
    assert result.state.capability_status == expected_status


def test_rt01_consumes_a_line_without_becoming_capability_semantics_owner() -> None:
    result = execute_subject_tick(_tick_input("a-line-role-boundary"))
    assert result.no_planner_orchestrator_dependency is True
    assert result.no_phase_semantics_override_dependency is True
    assert result.state.a_capability_status == result.a_line_result.state.capability_status.value
    assert any(
        checkpoint.checkpoint_id == "rt01.a_line_normalization_checkpoint"
        for checkpoint in result.state.execution_checkpoints
    )


def test_adversarial_capability_state_distinctions_are_path_visible() -> None:
    available_contract = _a_line_contract_result(
        "a-line-distinct-available-contract",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c04_mode="continue_stream",
        c05_action="reuse_without_revalidation",
    )
    policy_contract = _a_line_contract_result(
        "a-line-distinct-policy-contract",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c04_mode="continue_stream",
        c05_action="run_selective_revalidation",
    )
    underconstrained_contract = _a_line_contract_result(
        "a-line-distinct-underconstrained-contract",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c04_mode="continue_stream",
        c05_action="reuse_without_revalidation",
    )
    no_safe_contract = _a_line_contract_result(
        "a-line-distinct-nosafe-contract",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
        c04_mode="continue_stream",
        c05_action="reuse_without_revalidation",
    )

    policy_conditioned = execute_subject_tick(
        _tick_input("a-line-distinct-policy"),
        context=SubjectTickContext(
            require_a_line_capability_claim=True,
            dependency_trigger_hits=("trigger:mode_shift",),
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("a-line-distinct-policy"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-a-line-distinct-policy",
                    action_id="world-action-subject-tick-a-line-distinct-policy-1",
                    observed_at="2026-04-09T18:16:00+00:00",
                    source_ref="world.effect.sprint8c",
                    success=True,
                ),
            ),
        ),
    )
    underconstrained = execute_subject_tick(
        _tick_input("a-line-distinct-underconstrained"),
        context=SubjectTickContext(
            require_a_line_capability_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("a-line-distinct-underconstrained"),
            ),
        ),
    )
    no_safe = execute_subject_tick(
        _tick_input("a-line-distinct-nosafe"),
        context=SubjectTickContext(require_a_line_capability_claim=True),
    )

    assert available_contract.state.capability_status == CapabilityStatus.AVAILABLE_CAPABILITY
    assert available_contract.gate.available_capability_claim_allowed is True

    assert policy_contract.state.capability_status == CapabilityStatus.POLICY_CONDITIONED_CAPABILITY
    assert policy_contract.gate.policy_conditioned_capability_present is True
    assert policy_contract.gate.available_capability_claim_allowed is False

    assert underconstrained_contract.state.capability_status == CapabilityStatus.UNDERCONSTRAINED_CAPABILITY
    assert underconstrained_contract.gate.underconstrained_capability is True
    assert underconstrained_contract.gate.no_safe_capability_claim is False

    assert no_safe_contract.gate.no_safe_capability_claim is True
    assert no_safe_contract.gate.underconstrained_capability is False

    assert policy_conditioned.state.a_capability_status == CapabilityStatus.POLICY_CONDITIONED_CAPABILITY.value
    assert policy_conditioned.state.a_policy_conditioned_capability_present is True
    assert policy_conditioned.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert "policy_gated_capability_reframed_as_free_action" in policy_conditioned.state.a_forbidden_shortcuts

    assert underconstrained.state.a_capability_status == CapabilityStatus.UNDERCONSTRAINED_CAPABILITY.value
    assert underconstrained.state.a_underconstrained is True
    assert underconstrained.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert "underconstrained_capability_presented_as_ready" in underconstrained.state.a_forbidden_shortcuts

    assert no_safe.state.a_no_safe_capability_claim is True
    assert no_safe.state.a_capability_status in {
        CapabilityStatus.UNAVAILABLE_CAPABILITY.value,
        CapabilityStatus.NO_SAFE_CAPABILITY_CLAIM.value,
    }
    assert no_safe.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert "unavailable_capability_reframed_as_available" in no_safe.state.a_forbidden_shortcuts

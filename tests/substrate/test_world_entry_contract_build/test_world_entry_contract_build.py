from __future__ import annotations

from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    derive_runtime_dispatch_contract_view,
    dispatch_runtime_tick,
)
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    execute_subject_tick,
    subject_tick_result_to_payload,
)
from substrate.world_adapter import (
    WorldAdapterInput,
    build_world_effect_packet,
    build_world_observation_packet,
    run_world_adapter_cycle,
)
from substrate.world_entry_contract import (
    WorldClaimClass,
    WorldClaimStatus,
    build_world_entry_contract,
    derive_world_entry_contract_view,
    world_entry_contract_snapshot,
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
        source_ref="world.sensor.sprint8a",
        observed_at="2026-04-09T09:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def _matched_world_entry_contract(case_id: str):
    tick_id = f"tick-{case_id}"
    adapter_result = run_world_adapter_cycle(
        tick_id=tick_id,
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=_observation(case_id),
            effect_packet=build_world_effect_packet(
                effect_id=f"eff-{case_id}",
                action_id=f"world-action-{tick_id}",
                observed_at="2026-04-09T09:00:01+00:00",
                source_ref="world.effect.sprint8a",
                success=True,
            ),
        ),
        request_action_candidate=True,
        source_lineage=("test.world-entry",),
    )
    return build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=adapter_result,
        source_lineage=("test.w-entry-contract",),
    )


def test_world_entry_contract_materializes_typed_episode_and_view() -> None:
    contract = _matched_world_entry_contract("s8a-typed-episode")
    view = derive_world_entry_contract_view(contract)
    snapshot = world_entry_contract_snapshot(contract)
    assert contract.episode.world_episode_id.startswith("world-episode:")
    assert contract.episode.observation_basis_present is True
    assert contract.episode.action_trace_present is True
    assert contract.episode.effect_basis_present is True
    assert contract.episode.effect_feedback_correlated is True
    assert view.w01_admission_ready is True
    assert snapshot["w01_admission"]["admission_ready"] is True
    assert view.scope_marker == "rt01_contour_only"
    assert view.scope_rt01_contour_only is True
    assert view.scope_admission_layer_only is True
    assert view.scope_w01_implemented is False
    assert view.scope_w_line_implemented is False
    assert view.scope_repo_wide_adoption is False
    assert snapshot["scope_marker"]["scope"] == "rt01_contour_only"
    assert snapshot["scope_marker"]["admission_layer_only"] is True
    assert snapshot["scope_marker"]["w01_implemented"] is False
    assert snapshot["scope_marker"]["w_line_implemented"] is False
    assert snapshot["scope_marker"]["repo_wide_adoption"] is False


def test_forbidden_claims_machine_readable_when_world_basis_absent() -> None:
    adapter_result = run_world_adapter_cycle(
        tick_id="tick-s8a-no-world",
        execution_mode="continue_stream",
    )
    contract = build_world_entry_contract(
        tick_id="tick-s8a-no-world",
        world_adapter_result=adapter_result,
    )
    admissions = {entry.claim_class: entry for entry in contract.claim_admissions}
    assert admissions[WorldClaimClass.EXTERNALLY_EFFECTED_CHANGE_CLAIM].admitted is False
    assert admissions[WorldClaimClass.WORLD_GROUNDED_SUCCESS_CLAIM].admitted is False
    assert admissions[WorldClaimClass.WORLD_CALIBRATION_CLAIM].status in {
        WorldClaimStatus.NOT_ADMISSIBLE,
        WorldClaimStatus.UNDERCONSTRAINED,
    }
    assert WorldClaimClass.ENVIRONMENT_STATE_CHANGE_CLAIM.value in contract.forbidden_claim_classes
    assert contract.w01_admission.forbidden_claims_machine_readable is True
    assert contract.w01_admission.admission_ready is False


def test_effect_packet_without_action_linkage_cannot_admit_action_success_claim() -> None:
    adapter_result = run_world_adapter_cycle(
        tick_id="tick-s8a-orphan-effect",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=_observation("s8a-orphan-effect"),
            effect_packet=build_world_effect_packet(
                effect_id="eff-s8a-orphan-effect",
                action_id="nonexistent-action",
                observed_at="2026-04-09T09:00:02+00:00",
                source_ref="world.effect.sprint8a",
                success=True,
            ),
        ),
        request_action_candidate=False,
    )
    contract = build_world_entry_contract(
        tick_id="tick-s8a-orphan-effect",
        world_adapter_result=adapter_result,
    )
    admissions = {entry.claim_class: entry for entry in contract.claim_admissions}
    action_success = admissions[WorldClaimClass.ACTION_SUCCESS_IN_WORLD_CLAIM]
    assert action_success.admitted is False
    assert "action_trace_present" in action_success.missing_basis
    assert WorldClaimClass.ACTION_SUCCESS_IN_WORLD_CLAIM.value in contract.forbidden_claim_classes


def test_w_entry_admission_criteria_distinguish_observation_noise_from_linked_episode() -> None:
    observation_only = build_world_entry_contract(
        tick_id="tick-s8a-observation-only",
        world_adapter_result=run_world_adapter_cycle(
            tick_id="tick-s8a-observation-only",
            execution_mode="continue_stream",
            adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8a-observation-only"),
            ),
            request_action_candidate=False,
        ),
    )
    linked = _matched_world_entry_contract("s8a-linked")
    assert observation_only.w01_admission.admission_ready is False
    assert linked.w01_admission.admission_ready is True
    assert "w01_admission_requires_linked_observation_action_effect_episode" in (
        observation_only.w01_admission.restrictions
    )


def test_subject_tick_world_entry_contract_is_path_affecting_when_success_feedback_required() -> None:
    mismatch = execute_subject_tick(
        _tick_input("s8a-mismatch"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8a-mismatch"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-s8a-mismatch",
                    action_id="wrong-action-id",
                    observed_at="2026-04-09T09:00:03+00:00",
                    source_ref="world.effect.sprint8a",
                    success=True,
                ),
            ),
        ),
    )
    matched = execute_subject_tick(
        _tick_input("s8a-matched"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8a-matched"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-s8a-matched",
                    action_id="world-action-subject-tick-s8a-matched-1",
                    observed_at="2026-04-09T09:00:04+00:00",
                    source_ref="world.effect.sprint8a",
                    success=True,
                ),
            ),
        ),
    )
    assert mismatch.state.world_entry_world_effect_success_admissible is False
    assert mismatch.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert matched.state.world_entry_world_effect_success_admissible is True
    assert matched.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_world_entry_ablation_contrast_keeps_contract_visible() -> None:
    enforced = execute_subject_tick(
        _tick_input("s8a-ablation-enforced"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8a-ablation-enforced"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-s8a-ablation-enforced",
                    action_id="wrong-action-id",
                    observed_at="2026-04-09T09:00:05+00:00",
                    source_ref="world.effect.sprint8a",
                    success=True,
                ),
            ),
        ),
    )
    ablated = execute_subject_tick(
        _tick_input("s8a-ablation-disabled"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            emit_world_action_candidate=True,
            disable_world_seam_enforcement=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8a-ablation-disabled"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-s8a-ablation-disabled",
                    action_id="wrong-action-id",
                    observed_at="2026-04-09T09:00:06+00:00",
                    source_ref="world.effect.sprint8a",
                    success=True,
                ),
            ),
        ),
    )
    assert enforced.state.world_entry_world_effect_success_admissible is False
    assert ablated.state.world_entry_world_effect_success_admissible is False
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert ablated.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_no_world_requirement_regression_keeps_contour_compatible() -> None:
    result = execute_subject_tick(_tick_input("s8a-no-world-required"))
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert result.state.world_entry_episode_id.startswith("world-episode:")
    assert result.state.world_entry_w01_admission_ready is False


def test_runtime_dispatch_contract_surfaces_world_entry_admission_snapshot() -> None:
    dispatch = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("s8a-dispatch"),
            context=SubjectTickContext(
                require_world_grounded_transition=True,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=True,
                    adapter_available=True,
                    observation_packet=_observation("s8a-dispatch"),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    view = derive_runtime_dispatch_contract_view(dispatch)
    assert view.accepted is True
    assert view.world_entry_episode_id is not None
    assert view.world_entry_w01_admission_ready is False
    assert isinstance(view.world_entry_forbidden_claim_classes, tuple)
    assert view.world_entry_scope == "rt01_contour_only"
    assert view.world_entry_scope_admission_layer_only is True
    assert view.world_entry_scope_w01_implemented is False
    assert view.world_entry_scope_w_line_implemented is False
    assert view.world_entry_scope_repo_wide_adoption is False


def test_subject_tick_snapshot_carries_machine_readable_bounded_scope_marker() -> None:
    result = execute_subject_tick(
        _tick_input("s8a-snapshot-scope"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8a-snapshot-scope"),
            ),
        ),
    )
    payload = subject_tick_result_to_payload(result)
    state = payload["state"]
    assert state["world_entry_scope"] == "rt01_contour_only"
    assert state["world_entry_scope_admission_layer_only"] is True
    assert state["world_entry_scope_w01_implemented"] is False
    assert state["world_entry_scope_w_line_implemented"] is False
    assert state["world_entry_scope_repo_wide_adoption"] is False
    assert payload["world_entry_result"]["scope_marker"]["scope"] == "rt01_contour_only"

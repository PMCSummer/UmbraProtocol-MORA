from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    choose_runtime_execution_outcome_from_runtime_state,
    execute_subject_tick,
    persist_subject_tick_result_via_f01,
)
from substrate.world_adapter import (
    WorldAdapterInput,
    build_world_effect_packet,
    build_world_observation_packet,
)
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-subject-tick-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-06T00:00:00+00:00",
            event_id="ev-stage-subject-tick-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot


def test_stage_contour_f01_f02_r01_r02_r03_r04_c01_c02_c03_c04_c05_subject_tick_persistence_and_traceability() -> None:
    boot = _bootstrapped_state()
    start_revision = boot.state.runtime.revision
    tick = execute_subject_tick(
        SubjectTickInput(
            case_id="stage-subject-tick",
            energy=14.0,
            cognitive=95.0,
            safety=34.0,
            unresolved_preference=True,
        )
    )
    phases = tuple(step.phase_id for step in tick.state.downstream_step_results)
    assert phases == ("R", "C01", "C02", "C03", "C04", "C05")
    persisted = persist_subject_tick_result_via_f01(
        result=tick,
        runtime_state=boot.state,
        transition_id="tr-stage-subject-tick-persist",
        requested_at="2026-04-06T01:05:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["subject_tick_snapshot"]
    assert snapshot["state"]["tick_id"]
    assert snapshot["state"]["final_execution_outcome"] in {
        "continue",
        "repair",
        "revalidate",
        "halt",
    }
    assert persisted.state.domains.regulation.updated_by_phase == "R04"
    assert persisted.state.domains.continuity.updated_by_phase == "C04"
    assert persisted.state.domains.validity.updated_by_phase == "C05"
    assert choose_runtime_execution_outcome_from_runtime_state(persisted.state) in {
        "continue",
        "repair",
        "revalidate",
        "halt",
    }


def test_stage_contour_subject_tick_obeys_c04_and_c05_contract_changes() -> None:
    baseline = execute_subject_tick(
        SubjectTickInput(
            case_id="stage-subject-tick-baseline",
            energy=14.0,
            cognitive=95.0,
            safety=34.0,
            unresolved_preference=True,
        )
    )
    restricted = execute_subject_tick(
        SubjectTickInput(
            case_id="stage-subject-tick-restricted",
            energy=14.0,
            cognitive=95.0,
            safety=34.0,
            unresolved_preference=True,
        ),
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    assert baseline.state.c04_selected_mode
    assert baseline.state.c04_execution_mode_claim
    assert baseline.state.c04_authority_role == "arbitration"
    assert baseline.state.c05_authority_role == "invalidation"
    assert baseline.state.d01_authority_role == "observability_only"
    assert baseline.state.role_frontier_typed is True
    assert baseline.state.role_frontier_only is True
    assert baseline.state.role_map_ready is False
    assert restricted.state.c05_validity_action in {
        "run_selective_revalidation",
        "run_bounded_revalidation",
        "halt_reuse_and_rebuild_scope",
        "suspend_until_revalidation_basis",
    }
    assert restricted.state.c05_execution_action_claim == restricted.state.c05_validity_action
    assert any(
        checkpoint.checkpoint_id == "rt01.c05_legality_checkpoint"
        and checkpoint.status.value in {"enforced_detour", "blocked"}
        for checkpoint in restricted.state.execution_checkpoints
    )
    assert baseline.state.active_execution_mode != restricted.state.active_execution_mode


def test_stage_contour_world_seam_presence_changes_runtime_legality_path() -> None:
    absent = execute_subject_tick(
        SubjectTickInput(
            case_id="stage-subject-tick-world-absent",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
        ),
    )
    present = execute_subject_tick(
        SubjectTickInput(
            case_id="stage-subject-tick-world-present",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=build_world_observation_packet(
                    observation_id="obs-stage-world-present",
                    source_ref="world.sensor.stage",
                    observed_at="2026-04-08T20:05:00+00:00",
                    payload_ref="payload:stage-world-present",
                ),
            ),
        ),
    )
    assert absent.state.final_execution_outcome.value == "repair"
    assert present.state.final_execution_outcome.value == "continue"
    assert absent.state.world_entry_episode_id.startswith("world-episode:")
    assert present.state.world_entry_episode_id.startswith("world-episode:")
    assert any(
        checkpoint.checkpoint_id == "rt01.world_seam_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in absent.state.execution_checkpoints
    )
    assert any(
        checkpoint.checkpoint_id == "rt01.world_seam_checkpoint"
        and checkpoint.status.value == "allowed"
        for checkpoint in present.state.execution_checkpoints
    )
    assert any(
        checkpoint.checkpoint_id == "rt01.world_entry_checkpoint"
        for checkpoint in absent.state.execution_checkpoints
    )


def test_stage_contour_world_effect_action_mismatch_forces_revalidate_when_feedback_required() -> None:
    matched = execute_subject_tick(
        SubjectTickInput(
            case_id="stage-subject-tick-world-effect-matched",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=build_world_observation_packet(
                    observation_id="obs-stage-world-effect-matched",
                    source_ref="world.sensor.stage",
                    observed_at="2026-04-08T20:10:00+00:00",
                    payload_ref="payload:stage-world-effect-matched",
                ),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-stage-world-effect-matched",
                    action_id="world-action-subject-tick-stage-subject-tick-world-effect-matched-1",
                    observed_at="2026-04-08T20:10:01+00:00",
                    source_ref="world.effect.stage",
                    success=True,
                ),
            ),
        ),
    )
    mismatched = execute_subject_tick(
        SubjectTickInput(
            case_id="stage-subject-tick-world-effect-mismatch",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            require_world_effect_feedback_for_success_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=build_world_observation_packet(
                    observation_id="obs-stage-world-effect-mismatch",
                    source_ref="world.sensor.stage",
                    observed_at="2026-04-08T20:10:10+00:00",
                    payload_ref="payload:stage-world-effect-mismatch",
                ),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-stage-world-effect-mismatch",
                    action_id="wrong-action-id",
                    observed_at="2026-04-08T20:10:11+00:00",
                    source_ref="world.effect.stage",
                    success=True,
                ),
            ),
        ),
    )
    assert matched.state.world_effect_feedback_correlated is True
    assert matched.state.world_entry_world_effect_success_admissible is True
    assert matched.state.final_execution_outcome.value == "continue"
    assert mismatched.state.world_effect_feedback_correlated is False
    assert mismatched.state.world_externally_effected_change_claim_allowed is False
    assert mismatched.state.world_entry_world_effect_success_admissible is False
    assert mismatched.state.final_execution_outcome.value == "revalidate"
    assert any(
        checkpoint.checkpoint_id == "rt01.world_seam_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in mismatched.state.execution_checkpoints
    )

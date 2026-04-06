from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    execute_subject_tick,
    persist_subject_tick_result_via_f01,
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

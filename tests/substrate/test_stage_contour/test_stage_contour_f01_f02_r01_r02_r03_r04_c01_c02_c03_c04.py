from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.mode_arbitration import (
    ModeArbitrationContext,
    build_mode_arbitration,
    choose_subject_execution_mode,
    persist_mode_arbitration_result_via_f01,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition
from tests.substrate.c04_testkit import build_c04_upstream


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-c04-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-06T00:00:00+00:00",
            event_id="ev-stage-c04-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot


def test_stage_contour_f01_f02_r01_r02_r03_r04_c01_c02_c03_c04_persistence_and_traceability() -> None:
    boot = _bootstrapped_state()
    start_revision = boot.state.runtime.revision
    upstream = build_c04_upstream(
        case_id="stage-c04-first",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    c04 = build_mode_arbitration(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    assert c04.state.mode_priority_vector
    assert c04.telemetry.ledger_events
    persisted = persist_mode_arbitration_result_via_f01(
        result=c04,
        runtime_state=boot.state,
        transition_id="tr-stage-c04-persist",
        requested_at="2026-04-06T00:25:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["mode_arbitration_snapshot"]
    assert snapshot["state"]["arbitration_id"]
    assert snapshot["state"]["mode_priority_vector"]
    assert snapshot["telemetry"]["ledger_events"]


def test_stage_contour_c04_endogenous_tick_vs_external_reactive_non_equivalence() -> None:
    upstream = build_c04_upstream(
        case_id="stage-c04-tick-contrast",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    endogenous = build_mode_arbitration(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=ModeArbitrationContext(external_turn_present=False),
    )
    reactive_only = build_mode_arbitration(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=ModeArbitrationContext(
            external_turn_present=True,
            allow_endogenous_tick=False,
        ),
    )

    endogenous_mode = choose_subject_execution_mode(endogenous)
    reactive_mode = choose_subject_execution_mode(reactive_only)
    assert endogenous.state.endogenous_tick_allowed is True
    assert reactive_only.state.endogenous_tick_allowed is False
    assert endogenous_mode != reactive_mode or (
        endogenous.state.active_mode != reactive_only.state.active_mode
    )

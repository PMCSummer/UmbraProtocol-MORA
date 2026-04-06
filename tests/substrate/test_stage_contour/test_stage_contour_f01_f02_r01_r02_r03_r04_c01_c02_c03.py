from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.stream_diversification import (
    StreamDiversificationContext,
    build_stream_diversification,
    persist_stream_diversification_result_via_f01,
    select_alternative_path_candidates,
)
from substrate.tension_scheduler import TensionSchedulerContext, build_tension_scheduler
from substrate.transition import execute_transition
from tests.substrate.c03_testkit import build_c03_upstream


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-c03-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-06T00:00:00+00:00",
            event_id="ev-stage-c03-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot


def test_stage_contour_f01_f02_r01_r02_r03_r04_c01_c02_c03_persistence_and_traceability() -> None:
    boot = _bootstrapped_state()
    start_revision = boot.state.runtime.revision
    upstream = build_c03_upstream(
        case_id="stage-c03-first",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    c03 = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    assert c03.state.path_assessments
    assert c03.telemetry.ledger_events
    persisted = persist_stream_diversification_result_via_f01(
        result=c03,
        runtime_state=boot.state,
        transition_id="tr-stage-c03-persist",
        requested_at="2026-04-06T00:15:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["stream_diversification_snapshot"]
    assert snapshot["state"]["diversification_id"]
    assert snapshot["state"]["path_assessments"]
    assert snapshot["telemetry"]["ledger_events"]


def test_stage_contour_c03_distinguishes_rumination_from_justified_recurrence() -> None:
    seed = build_c03_upstream(
        case_id="stage-c03-seed",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    prior = build_stream_diversification(
        seed.stream,
        seed.scheduler,
        seed.regulation,
        seed.affordances,
        seed.preferences,
        seed.viability,
    )

    ruminative_scheduler = build_tension_scheduler(
        seed.stream,
        seed.regulation,
        seed.affordances,
        seed.preferences,
        seed.viability,
        context=TensionSchedulerContext(prior_scheduler_state=seed.scheduler.state),
    )
    ruminative = build_stream_diversification(
        seed.stream,
        ruminative_scheduler,
        seed.regulation,
        seed.affordances,
        seed.preferences,
        seed.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )

    justified_scheduler = build_tension_scheduler(
        seed.stream,
        seed.regulation,
        seed.affordances,
        seed.preferences,
        seed.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=seed.scheduler.state,
            explicit_wake_triggers=("defer_window_expiry",),
            wake_anchor_scope=(seed.scheduler.state.tensions[0].causal_anchor,),
        ),
    )
    justified = build_stream_diversification(
        seed.stream,
        justified_scheduler,
        seed.regulation,
        seed.affordances,
        seed.preferences,
        seed.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )

    assert ruminative.state.diversification_pressure >= justified.state.diversification_pressure
    assert len(select_alternative_path_candidates(ruminative)) >= len(
        select_alternative_path_candidates(justified)
    )

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.stream_kernel import StreamKernelContext, build_stream_kernel
from substrate.tension_scheduler import (
    TensionSchedulerContext,
    build_tension_scheduler,
    persist_tension_scheduler_result_via_f01,
    select_revisit_tensions,
)
from substrate.transition import execute_transition
from tests.substrate.c01_testkit import build_c01_upstream


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-c02-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-06T00:00:00+00:00",
            event_id="ev-stage-c02-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot


def test_stage_contour_f01_f02_r01_r02_r03_r04_c01_c02_persistence_and_traceability() -> None:
    boot = _bootstrapped_state()
    start_revision = boot.state.runtime.revision
    upstream = build_c01_upstream(
        case_id="stage-c02-first",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    stream = build_stream_kernel(
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    scheduler = build_tension_scheduler(
        stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )

    assert scheduler.state.tensions
    assert scheduler.telemetry.ledger_events
    persisted = persist_tension_scheduler_result_via_f01(
        result=scheduler,
        runtime_state=boot.state,
        transition_id="tr-stage-c02-persist",
        requested_at="2026-04-06T00:15:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["tension_scheduler_snapshot"]
    assert snapshot["state"]["scheduler_id"]
    assert snapshot["state"]["tensions"]
    assert snapshot["telemetry"]["ledger_events"]


def test_stage_contour_c01_c02_revisit_is_scheduled_not_retrieval_driven() -> None:
    pressure = build_c01_upstream(
        case_id="stage-c02-pressure",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    stream1 = build_stream_kernel(
        pressure.regulation,
        pressure.affordances,
        pressure.preferences,
        pressure.viability,
    )
    c02_1 = build_tension_scheduler(
        stream1,
        pressure.regulation,
        pressure.affordances,
        pressure.preferences,
        pressure.viability,
    )
    first_anchor = c02_1.state.tensions[0].causal_anchor

    c02_2 = build_tension_scheduler(
        stream1,
        pressure.regulation,
        pressure.affordances,
        pressure.preferences,
        pressure.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=c02_1.state,
            closure_evidence_anchor_keys=(first_anchor,),
        ),
    )
    c02_3 = build_tension_scheduler(
        stream1,
        pressure.regulation,
        pressure.affordances,
        pressure.preferences,
        pressure.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=c02_2.state,
            retrieved_episode_refs=(first_anchor,),
        ),
    )
    c02_4 = build_tension_scheduler(
        stream1,
        pressure.regulation,
        pressure.affordances,
        pressure.preferences,
        pressure.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=c02_2.state,
            reopen_anchor_keys=(first_anchor,),
        ),
    )

    entry_retrieval = next(
        entry for entry in c02_3.state.tensions if entry.causal_anchor == first_anchor
    )
    entry_reopen = next(
        entry for entry in c02_4.state.tensions if entry.causal_anchor == first_anchor
    )
    assert entry_retrieval.current_status.value == "closed"
    assert entry_retrieval.scheduling_mode.value == "monitor_passively"
    assert entry_reopen.current_status.value == "reactivated"
    assert select_revisit_tensions(c02_4)

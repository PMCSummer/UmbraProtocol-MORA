from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.stream_kernel import (
    StreamKernelContext,
    build_stream_kernel,
    persist_stream_kernel_result_via_f01,
)
from substrate.transition import execute_transition
from tests.substrate.c01_testkit import build_c01_upstream


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-c01-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-05T00:00:00+00:00",
            event_id="ev-stage-c01-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot


def test_stage_contour_f01_f02_r01_r02_r03_r04_c01_persistence_and_kernel_traceability() -> None:
    boot = _bootstrapped_state()
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)
    first_upstream = build_c01_upstream(
        case_id="stage-c01-first",
        energy=16.0,
        cognitive=94.0,
        safety=36.0,
        unresolved_preference=True,
    )
    first = build_stream_kernel(
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
    )

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert first.no_downstream_scheduler_selection_performed is True
    assert first.state.carryover_items
    assert first.telemetry.ledger_events
    assert first.state.source_viability_ref.startswith("viability:")

    persisted = persist_stream_kernel_result_via_f01(
        result=first,
        runtime_state=boot.state,
        transition_id="tr-stage-c01-persist",
        requested_at="2026-04-05T00:15:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["stream_kernel_snapshot"]
    assert snapshot["state"]["stream_id"]
    assert snapshot["state"]["carryover_items"]
    assert snapshot["state"]["link_decision"]
    assert snapshot["telemetry"]["ledger_events"]


def test_stage_contour_c01_relevant_pressure_persists_but_old_memory_recall_not_treated_as_active_stream() -> None:
    first_upstream = build_c01_upstream(
        case_id="stage-c01-pressure",
        energy=16.0,
        cognitive=94.0,
        safety=36.0,
        unresolved_preference=True,
    )
    first = build_stream_kernel(
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
    )
    second = build_stream_kernel(
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
        context=StreamKernelContext(prior_stream_state=first.state),
    )
    settled_upstream = build_c01_upstream(
        case_id="stage-c01-settled",
        energy=57.0,
        cognitive=46.0,
        safety=71.0,
        unresolved_preference=False,
    )
    third = build_stream_kernel(
        settled_upstream.regulation,
        settled_upstream.affordances,
        settled_upstream.preferences,
        settled_upstream.viability,
        context=StreamKernelContext(
            prior_stream_state=second.state,
            source_lineage=("memory-recall-only",),
            require_strong_link=True,
        ),
    )

    assert second.state.carryover_items
    assert third.state.link_decision.value in {
        "ambiguous_link",
        "forced_new_stream",
        "forced_release",
    }
    assert "memory-recall-only" in third.state.source_lineage

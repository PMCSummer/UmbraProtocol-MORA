from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.temporal_validity import (
    TemporalValidityContext,
    build_temporal_validity,
    can_continue_mode_hold,
    can_open_branch_access,
    can_revisit_with_basis,
    persist_temporal_validity_result_via_f01,
    select_revalidation_targets,
)
from substrate.transition import execute_transition
from tests.substrate.c05_testkit import build_c05_upstream


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-c05-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-06T00:00:00+00:00",
            event_id="ev-stage-c05-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot


def test_stage_contour_f01_f02_r01_r02_r03_r04_c01_c02_c03_c04_c05_persistence_and_traceability() -> None:
    boot = _bootstrapped_state()
    start_revision = boot.state.runtime.revision
    upstream = build_c05_upstream(
        case_id="stage-c05-first",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    c05 = build_temporal_validity(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.mode_arbitration,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    assert c05.state.items
    assert c05.telemetry.ledger_events
    persisted = persist_temporal_validity_result_via_f01(
        result=c05,
        runtime_state=boot.state,
        transition_id="tr-stage-c05-persist",
        requested_at="2026-04-06T00:35:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["temporal_validity_snapshot"]
    assert snapshot["state"]["validity_id"]
    assert snapshot["state"]["items"]
    assert snapshot["telemetry"]["ledger_events"]


def test_stage_contour_c05_selective_revalidation_changes_permissions_without_blanket_reset() -> None:
    upstream = build_c05_upstream(
        case_id="stage-c05-selective",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    baseline = build_temporal_validity(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.mode_arbitration,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    selective = build_temporal_validity(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.mode_arbitration,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TemporalValidityContext(
            prior_temporal_validity_state=baseline.state,
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    full_like = build_temporal_validity(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.mode_arbitration,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TemporalValidityContext(
            prior_temporal_validity_state=baseline.state,
            dependency_trigger_hits=("trigger:mode_shift",),
            disable_selective_scope_handling=True,
        ),
    )

    assert len(select_revalidation_targets(selective)) <= len(select_revalidation_targets(full_like))
    assert (
        can_continue_mode_hold(baseline),
        can_revisit_with_basis(baseline),
        can_open_branch_access(baseline),
    ) != (
        can_continue_mode_hold(selective),
        can_revisit_with_basis(selective),
        can_open_branch_access(selective),
    )

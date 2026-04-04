from __future__ import annotations

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.discourse_update import persist_discourse_update_result_via_f01
from substrate.state import create_empty_state
from substrate.transition import execute_transition
from tests.substrate.l06_testkit import build_l06_context


def test_l06_roundtrip_persistence_snapshot_stable() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l06-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-05T00:00:00+00:00",
            event_id="ev-l06-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True

    result = build_l06_context('he said "you are tired?"', "l06-roundtrip").discourse_update
    persisted = persist_discourse_update_result_via_f01(
        result=result,
        runtime_state=boot.state,
        transition_id="tr-l06-roundtrip-persist",
        requested_at="2026-04-05T00:10:00+00:00",
    )

    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    snapshot = persisted.state.trace.events[-1].payload["discourse_update_snapshot"]
    assert snapshot["bundle"]["update_proposals"]
    assert snapshot["bundle"]["interpretation_not_equal_accepted_update"] is True
    assert snapshot["bundle"]["downstream_update_acceptor_absent"] is True
    assert snapshot["bundle"]["repair_consumer_absent"] is True
    assert snapshot["bundle"]["legacy_g01_bypass_risk_present"] is True
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]

from __future__ import annotations

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.modus_hypotheses import (
    persist_modus_hypothesis_result_via_f01,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition
from tests.substrate.l05_testkit import build_l05_context


def test_l05_roundtrip_persistence_snapshot_stable() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l05-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-l05-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True

    result = build_l05_context('he said "you are tired"', "l05-roundtrip").modus
    persisted = persist_modus_hypothesis_result_via_f01(
        result=result,
        runtime_state=boot.state,
        transition_id="tr-l05-roundtrip-persist",
        requested_at="2026-04-04T00:10:00+00:00",
    )

    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    snapshot = persisted.state.trace.events[-1].payload["modus_hypothesis_snapshot"]
    assert snapshot["bundle"]["hypothesis_records"]
    assert snapshot["bundle"]["l06_downstream_not_bound_here"] is True
    assert snapshot["bundle"]["l06_update_consumer_not_wired_here"] is True
    assert snapshot["bundle"]["l06_repair_consumer_not_wired_here"] is True
    assert snapshot["bundle"]["legacy_l04_g01_shortcut_operational_debt"] is True
    assert snapshot["bundle"]["legacy_shortcut_bypass_risk"] is True
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]

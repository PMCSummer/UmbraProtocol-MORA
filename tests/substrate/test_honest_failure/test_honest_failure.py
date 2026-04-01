from dataclasses import replace

from substrate.contracts import (
    FailureCode,
    ProvenanceStatus,
    TransitionKind,
    TransitionRequest,
    WriterIdentity,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_honest_failure_on_bad_request_shape() -> None:
    state = create_empty_state()
    bad_request = {"transition_kind": "INGEST_EXTERNAL_EVENT"}

    result = execute_transition(bad_request, state)

    assert result.accepted is False
    assert result.failure is not None
    assert result.failure.code == FailureCode.INVALID_REQUEST_SHAPE
    assert result.provenance.status == ProvenanceStatus.REJECTED
    assert result.state.failures.current is not None


def test_honest_failure_on_bad_state_shape() -> None:
    state = create_empty_state()
    invalid_state = replace(state, runtime=replace(state.runtime, revision=-1))
    request = TransitionRequest(
        transition_id="tr-invalid-state",
        transition_kind=TransitionKind.BOOTSTRAP_INIT,
        writer=WriterIdentity.BOOTSTRAPPER,
        cause_chain=("bootstrap-sequence",),
        requested_at="2026-04-01T00:05:00+00:00",
        event_id="ev-invalid-state",
        event_payload={"schema_version": "f01"},
    )

    result = execute_transition(request, invalid_state)

    assert result.accepted is False
    assert result.failure is not None
    assert result.failure.code == FailureCode.INVALID_STATE_SHAPE
    assert result.provenance.status == ProvenanceStatus.REJECTED


def test_success_without_provenance_cannot_be_returned() -> None:
    request = TransitionRequest(
        transition_id="tr-provenance-guard",
        transition_kind=TransitionKind.BOOTSTRAP_INIT,
        writer=WriterIdentity.BOOTSTRAPPER,
        cause_chain=("bootstrap-sequence",),
        requested_at="2026-04-01T00:06:00+00:00",
        event_id="ev-provenance-guard",
        event_payload={"schema_version": "f01"},
    )

    result = execute_transition(request, create_empty_state())

    assert result.accepted is True
    assert result.provenance is not None
    assert result.provenance.transition_id == result.state.runtime.last_transition_id

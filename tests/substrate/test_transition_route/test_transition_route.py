from dataclasses import FrozenInstanceError

import pytest

from substrate.contracts import ProvenanceStatus, TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    bootstrap_request = TransitionRequest(
        transition_id="tr-bootstrap-2",
        transition_kind=TransitionKind.BOOTSTRAP_INIT,
        writer=WriterIdentity.BOOTSTRAPPER,
        cause_chain=("bootstrap-sequence",),
        requested_at="2026-04-01T00:00:00+00:00",
        event_id="ev-bootstrap-2",
        event_payload={"schema_version": "f01"},
    )
    result = execute_transition(bootstrap_request, create_empty_state())
    assert result.accepted is True
    return result.state


def test_valid_ingest_transition_produces_delta_and_provenance() -> None:
    state = _bootstrapped_state()
    request = TransitionRequest(
        transition_id="tr-ingest-1",
        transition_kind=TransitionKind.INGEST_EXTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=("external-event", "integration-test"),
        requested_at="2026-04-01T00:01:00+00:00",
        event_id="ev-ingest-1",
        event_payload={"turn_id": "turn-1", "payload": "opaque"},
    )

    result = execute_transition(request, state)

    assert result.accepted is True
    assert result.authority.allowed is True
    assert result.state.turn.current_turn_id == "turn-1"
    assert result.state.turn.last_event_ref == "ev-ingest-1"
    assert result.delta.before_revision + 1 == result.delta.after_revision
    assert "turn.current_turn_id" in result.delta.changed_fields
    assert result.provenance is not None
    assert result.provenance.status == ProvenanceStatus.APPLIED
    assert result.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert result.provenance.cause_chain == ("external-event", "integration-test")
    assert result.authority.reason == "writer authorized"
    assert result.emitted_event.event_id == result.state.runtime.last_event_id
    assert result.state.runtime.last_transition_id == "tr-ingest-1"


def test_bypass_direct_mutation_is_impossible() -> None:
    state = create_empty_state()

    with pytest.raises(FrozenInstanceError):
        state.runtime.revision = 100

    with pytest.raises(FrozenInstanceError):
        state.turn.current_turn_id = "turn-direct-write"

    with pytest.raises(AttributeError):
        state.trace.events.append("ev-illegal")


def test_bypass_deep_mutation_of_event_payload_is_blocked() -> None:
    state = _bootstrapped_state()

    with pytest.raises(TypeError):
        state.trace.events[-1].payload["tamper"] = "x"

from substrate.contracts import (
    FailureCode,
    ProvenanceStatus,
    TransitionKind,
    TransitionRequest,
    WriterIdentity,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    bootstrap_request = TransitionRequest(
        transition_id="tr-bootstrap-3",
        transition_kind=TransitionKind.BOOTSTRAP_INIT,
        writer=WriterIdentity.BOOTSTRAPPER,
        cause_chain=("bootstrap-sequence",),
        requested_at="2026-04-01T00:00:00+00:00",
        event_id="ev-bootstrap-3",
        event_payload={"schema_version": "f01"},
    )
    result = execute_transition(bootstrap_request, create_empty_state())
    assert result.accepted is True
    return result.state


def test_invalid_authority_rejects_without_silent_turn_mutation() -> None:
    state = _bootstrapped_state()
    request = TransitionRequest(
        transition_id="tr-ingest-observer",
        transition_kind=TransitionKind.INGEST_EXTERNAL_EVENT,
        writer=WriterIdentity.OBSERVER,
        cause_chain=("external-event",),
        requested_at="2026-04-01T00:02:00+00:00",
        event_id="ev-ingest-observer",
        event_payload={"turn_id": "turn-x"},
    )

    result = execute_transition(request, state)

    assert result.accepted is False
    assert result.failure is not None
    assert result.failure.code == FailureCode.AUTHORITY_DENIED
    assert result.authority.allowed is False
    assert set(result.authority.denied_paths) == {
        "turn.current_turn_id",
        "turn.last_event_ref",
    }
    assert result.authority.reason == "writer attempted forbidden field writes"
    assert result.state.turn.current_turn_id == state.turn.current_turn_id
    assert result.state.turn.last_event_ref == state.turn.last_event_ref
    assert result.provenance.status == ProvenanceStatus.REJECTED


def test_same_event_contrasts_under_different_authority_rules() -> None:
    state = _bootstrapped_state()
    payload = {"turn_id": "turn-shared"}

    allowed = execute_transition(
        TransitionRequest(
            transition_id="tr-contrast-allowed",
            transition_kind=TransitionKind.INGEST_EXTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("external-event", "contrast"),
            requested_at="2026-04-01T00:03:00+00:00",
            event_id="ev-contrast-1",
            event_payload=payload,
        ),
        state,
    )
    denied = execute_transition(
        TransitionRequest(
            transition_id="tr-contrast-denied",
            transition_kind=TransitionKind.INGEST_EXTERNAL_EVENT,
            writer=WriterIdentity.OBSERVER,
            cause_chain=("external-event", "contrast"),
            requested_at="2026-04-01T00:03:30+00:00",
            event_id="ev-contrast-2",
            event_payload=payload,
        ),
        state,
    )

    assert allowed.accepted is True
    assert allowed.state.turn.current_turn_id == "turn-shared"
    assert denied.accepted is False
    assert denied.state.turn.current_turn_id == state.turn.current_turn_id

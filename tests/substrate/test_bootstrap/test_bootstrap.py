from substrate.contracts import ProvenanceStatus, TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_bootstrap_init_writes_expected_substrate_fields() -> None:
    state = create_empty_state()
    request = TransitionRequest(
        transition_id="tr-bootstrap-1",
        transition_kind=TransitionKind.BOOTSTRAP_INIT,
        writer=WriterIdentity.BOOTSTRAPPER,
        cause_chain=("bootstrap-sequence",),
        requested_at="2026-04-01T00:00:00+00:00",
        event_id="ev-bootstrap-1",
        event_payload={"schema_version": "f01"},
    )

    result = execute_transition(request, state)

    assert result.accepted is True
    assert result.failure is None
    assert result.authority.allowed is True
    assert result.state.meta.schema_version == "f01"
    assert result.state.meta.initialized_at == "2026-04-01T00:00:00+00:00"
    assert result.state.runtime.lifecycle.value == "INITIALIZED"
    assert result.provenance.status == ProvenanceStatus.APPLIED
    assert result.provenance.transition_kind == TransitionKind.BOOTSTRAP_INIT
    assert "meta.schema_version" in result.delta.changed_fields
    assert "trace.transitions" in result.delta.changed_fields

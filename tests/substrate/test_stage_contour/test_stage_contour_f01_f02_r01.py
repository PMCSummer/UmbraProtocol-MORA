from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.epistemics import (
    ConfidenceLevel,
    EpistemicStatus,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.regulation import (
    NeedAxis,
    NeedSignal,
    RegulationContext,
    persist_regulation_result_via_f01,
    update_regulation_state,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_r01_integration_uses_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-01T00:00:00+00:00",
            event_id="ev-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-stage-1", content="signal:energy-low"),
        SourceMetadata(
            source_id="sensor-stage-1",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            confidence_hint=ConfidenceLevel.HIGH,
        ),
    )
    assert epistemic.unit.status == EpistemicStatus.OBSERVATION

    regulation = update_regulation_state(
        signals=(
            NeedSignal(
                axis=NeedAxis.ENERGY,
                value=20.0,
                source_ref=epistemic.unit.unit_id,
            ),
        ),
        prior_state=None,
        context=RegulationContext(
            step_delta=1,
            source_lineage=(boot.provenance.transition_id, epistemic.unit.unit_id),
            require_strong_claim=False,
        ),
    )
    persisted = persist_regulation_result_via_f01(
        result=regulation,
        runtime_state=boot.state,
        transition_id="tr-stage-r01",
        requested_at="2026-04-01T00:10:00+00:00",
    )

    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.last_transition_id == "tr-stage-r01"
    event_payload = persisted.state.trace.events[-1].payload
    assert "regulation_snapshot" in event_payload
    assert event_payload["regulation_snapshot"]["bias"]["coping_mode"] == regulation.bias.coping_mode
    assert event_payload["regulation_snapshot"]["bias"]["restrictions"] == regulation.bias.restrictions
    assert epistemic.unit.status == EpistemicStatus.OBSERVATION

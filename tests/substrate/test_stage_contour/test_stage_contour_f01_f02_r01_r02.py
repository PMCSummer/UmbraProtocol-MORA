from substrate.affordances import (
    create_default_capability_state,
    generate_regulation_affordances,
    persist_affordance_result_via_f01,
)
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
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_r01_r02_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-r02-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-01T00:00:00+00:00",
            event_id="ev-stage-r02-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    boot_revision = boot.state.runtime.revision

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-stage-r02", content="signal:overload"),
        SourceMetadata(
            source_id="sensor-stage-r02",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            confidence_hint=ConfidenceLevel.HIGH,
        ),
    )
    assert epistemic.unit.status == EpistemicStatus.OBSERVATION

    regulation = update_regulation_state(
        signals=(
            NeedSignal(
                axis=NeedAxis.COGNITIVE_LOAD,
                value=88.0,
                source_ref=epistemic.unit.unit_id,
            ),
            NeedSignal(axis=NeedAxis.ENERGY, value=24.0, source_ref=epistemic.unit.unit_id),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=(epistemic.unit.unit_id,)),
    )
    affordances = generate_regulation_affordances(
        regulation_state=regulation.state,
        capability_state=create_default_capability_state(),
    )
    assert affordances.summary.total_candidates >= 2
    assert affordances.gate.reason.startswith("candidate landscape")
    assert boot.state.runtime.revision == boot_revision

    persisted = persist_affordance_result_via_f01(
        result=affordances,
        runtime_state=boot.state,
        transition_id="tr-stage-r02-persist",
        requested_at="2026-04-01T00:30:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == boot_revision + 1
    assert persisted.state.trace.events[-1].payload["affordance_snapshot"]["summary"][
        "total_candidates"
    ] == affordances.summary.total_candidates

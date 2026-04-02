from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    persist_preference_result_via_f01,
    update_regulatory_preferences,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_r01_r02_r03_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-r03-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-stage-r03-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-stage-r03", content="signal:overload and low energy"),
        SourceMetadata(
            source_id="sensor-stage-r03",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            confidence_hint=ConfidenceLevel.HIGH,
        ),
    )
    regulation = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=90.0, source_ref=epistemic.unit.unit_id),
            NeedSignal(axis=NeedAxis.ENERGY, value=18.0, source_ref=epistemic.unit.unit_id),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=(epistemic.unit.unit_id,)),
    )
    affordances = generate_regulation_affordances(
        regulation_state=regulation.state,
        capability_state=create_default_capability_state(),
    )
    candidate = affordances.candidates[0]
    preference_result = update_regulatory_preferences(
        regulation_state=regulation.state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-stage-r03",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("stage-contour",),
                observed_short_term_delta=0.72,
                observed_long_term_delta=0.52,
                attribution_confidence=regulation.state.confidence,
                source_ref=epistemic.unit.unit_id,
                provenance="stage-r03",
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=(epistemic.unit.unit_id,)),
    )

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert preference_result.updated_preference_state.entries

    persisted = persist_preference_result_via_f01(
        result=preference_result,
        runtime_state=boot.state,
        transition_id="tr-stage-r03-persist",
        requested_at="2026-04-02T00:15:00+00:00",
    )

    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["preference_snapshot"]
    assert snapshot["no_final_selection_performed"] is True
    assert snapshot["preference_state"]["entries"]
    assert snapshot["update_events"]
    assert snapshot["telemetry"]["attempted_update_paths"]
    entry = snapshot["preference_state"]["entries"][0]
    assert entry["option_class_id"] == candidate.option_class.value
    assert "episode:ep-stage-r03" in entry["last_update_provenance"]

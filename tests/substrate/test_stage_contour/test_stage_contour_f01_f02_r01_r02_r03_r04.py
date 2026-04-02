import pytest

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
    update_regulatory_preferences,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition
from substrate.viability_control import (
    ViabilityContext,
    compute_viability_control_state,
    persist_viability_control_result_via_f01,
)


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-r04-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-stage-r04-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot


def _contour_bundle(*, energy: float, cognitive: float, safety: float):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-stage-r04", content="vital signal stream"),
        SourceMetadata(
            source_id="sensor-stage-r04",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            confidence_hint=ConfidenceLevel.HIGH,
        ),
    )
    regulation = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref=epistemic.unit.unit_id),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref=epistemic.unit.unit_id),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref=epistemic.unit.unit_id),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=(epistemic.unit.unit_id,)),
    )
    affordances = generate_regulation_affordances(
        regulation_state=regulation.state,
        capability_state=create_default_capability_state(),
    )
    candidate = affordances.candidates[0]
    preferences = update_regulatory_preferences(
        regulation_state=regulation.state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-stage-r04",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("stage-r04",),
                observed_short_term_delta=0.55,
                observed_long_term_delta=0.3,
                attribution_confidence=regulation.state.confidence,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=(epistemic.unit.unit_id,)),
    )
    viability = compute_viability_control_state(
        regulation,
        affordances,
        preferences,
        context=ViabilityContext(source_lineage=(epistemic.unit.unit_id,)),
    )
    return epistemic, regulation, affordances, preferences, viability


def test_stage_contour_f01_f02_r01_r02_r03_r04_persistence_and_traceability() -> None:
    boot = _bootstrapped_state()
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)
    epistemic, _, _, _, viability = _contour_bundle(energy=16.0, cognitive=94.0, safety=35.0)

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert viability.no_action_selection_performed is True
    assert not hasattr(viability, "selected_action")
    assert viability.state.input_regulation_snapshot_ref.startswith("regulation-step-")

    persisted = persist_viability_control_result_via_f01(
        result=viability,
        runtime_state=boot.state,
        transition_id="tr-stage-r04-persist",
        requested_at="2026-04-04T00:15:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT

    snapshot = persisted.state.trace.events[-1].payload["viability_control_snapshot"]
    assert snapshot["state"]["pressure_level"] >= 0.0
    assert snapshot["state"]["escalation_stage"]
    assert snapshot["state"]["override_scope"]
    assert snapshot["state"]["deescalation_conditions"] is not None
    assert snapshot["telemetry"]["attempted_computation_paths"]
    assert epistemic.unit.unit_id in snapshot["telemetry"]["source_lineage"]


def test_stage_contour_r04_replay_preserves_pressure_when_deficit_unresolved() -> None:
    _, regulation1, affordances1, preferences1, step1 = _contour_bundle(
        energy=15.0,
        cognitive=95.0,
        safety=34.0,
    )
    _, regulation2, affordances2, preferences2, step2 = _contour_bundle(
        energy=16.0,
        cognitive=93.0,
        safety=36.0,
    )
    replay = compute_viability_control_state(
        regulation2,
        affordances2,
        preferences2,
        context=ViabilityContext(
            prior_regulation_state=regulation1.state,
            prior_viability_state=step1.state,
            recent_failed_recovery_attempts=2,
            source_lineage=("stage-r04-replay",),
        ),
    )
    assert replay.state.pressure_level >= step2.state.pressure_level or replay.state.persistence_state.value in {"persistent", "chronic"}


def test_stage_contour_r04_typed_only_path_rejects_raw_bypass() -> None:
    with pytest.raises(TypeError):
        compute_viability_control_state("raw", "raw", "raw")

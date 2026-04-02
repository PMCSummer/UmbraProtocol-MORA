from substrate.affordances import (
    AffordanceContext,
    AffordanceOptionClass,
    AffordanceStatus,
    CapabilitySpec,
    CapabilityState,
    create_default_capability_state,
    generate_regulation_affordances,
)
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    PreferenceSign,
    PreferenceUncertainty,
    PreferenceUpdateKind,
    persist_preference_result_via_f01,
    update_regulatory_preferences,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-contour-reg-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-contour-reg-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _sensor_unit(content: str, material_id: str):
    return ground_epistemic_input(
        InputMaterial(material_id=material_id, content=content),
        SourceMetadata(
            source_id=f"sensor-{material_id}",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            confidence_hint=ConfidenceLevel.HIGH,
        ),
    )


def _regulation_state(unit_id: str, *, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref=unit_id),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref=unit_id),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref=unit_id),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=(unit_id,)),
    ).state


def _first_available(result):
    available = [candidate for candidate in result.candidates if candidate.status == AffordanceStatus.AVAILABLE]
    return available[0] if available else result.candidates[0]


def test_regulation_contour_replay_load_bearing_scenarios() -> None:
    sensor = _sensor_unit("regulation tick", "m-reg-replay")
    assert sensor.unit.status.value == "observation"

    regulation_state = _regulation_state(
        sensor.unit.unit_id, energy=20.0, cognitive=89.0, safety=42.0
    )
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    assert affordances.summary.no_selection_performed is True
    assert not hasattr(affordances, "selected_affordance")
    base_candidate = _first_available(affordances)

    context = PreferenceContext(source_lineage=(sensor.unit.unit_id,), decay_per_step=0.0)
    step1 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-clean-1",
                option_class_id=base_candidate.option_class,
                affordance_id=base_candidate.affordance_id,
                target_need_or_set=base_candidate.target_axes,
                context_scope=("clean",),
                observed_short_term_delta=0.75,
                observed_long_term_delta=0.55,
                attribution_confidence=RegulationConfidence.HIGH,
                source_ref=sensor.unit.unit_id,
                observed_at_step=1,
            ),
        ),
        context=context,
    )
    step2 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-clean-2",
                option_class_id=base_candidate.option_class,
                affordance_id=base_candidate.affordance_id,
                target_need_or_set=base_candidate.target_axes,
                context_scope=("clean",),
                observed_short_term_delta=0.8,
                observed_long_term_delta=0.6,
                attribution_confidence=RegulationConfidence.HIGH,
                source_ref=sensor.unit.unit_id,
                observed_at_step=2,
            ),
        ),
        preference_state=step1.updated_preference_state,
        context=context,
    )
    clean_entry = step2.updated_preference_state.entries[0]
    assert clean_entry.preference_sign == PreferenceSign.POSITIVE
    assert clean_entry.episode_support >= 2

    mixed = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-mixed",
                option_class_id=base_candidate.option_class,
                affordance_id=base_candidate.affordance_id,
                target_need_or_set=base_candidate.target_axes,
                context_scope=("mixed",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                mixed_causes=True,
                observed_at_step=3,
            ),
        ),
        preference_state=step2.updated_preference_state,
        context=context,
    )
    assert mixed.blocked_updates
    assert mixed.blocked_updates[0].uncertainty == PreferenceUncertainty.ATTRIBUTION_BLOCKED

    delayed = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-delayed",
                option_class_id=base_candidate.option_class,
                affordance_id=base_candidate.affordance_id,
                target_need_or_set=base_candidate.target_axes,
                context_scope=("delayed",),
                observed_short_term_delta=0.2,
                observed_long_term_delta=None,
                attribution_confidence=RegulationConfidence.MEDIUM,
                delayed_window_complete=False,
                observed_at_step=4,
            ),
        ),
        preference_state=mixed.updated_preference_state,
        context=context,
    )
    assert delayed.blocked_updates
    assert delayed.blocked_updates[0].uncertainty == PreferenceUncertainty.DELAYED_EFFECT_UNRESOLVED

    conflict = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-short-vs-long",
                option_class_id=base_candidate.option_class,
                affordance_id=base_candidate.affordance_id,
                target_need_or_set=base_candidate.target_axes,
                context_scope=("clean",),
                observed_short_term_delta=0.8,
                observed_long_term_delta=-1.0,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=5,
            ),
        ),
        preference_state=delayed.updated_preference_state,
        context=context,
    )
    assert conflict.updated_preference_state.conflict_index
    assert any(
        event.update_kind
        in {PreferenceUpdateKind.CONFLICT_REGISTER, PreferenceUpdateKind.FREEZE, PreferenceUpdateKind.INVERT}
        for event in conflict.update_events
    )
    assert conflict.no_final_selection_performed is True
    assert not hasattr(conflict, "selected_action")

    constrained = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
        context=AffordanceContext(max_risk_tolerance=0.2),
    )
    assert any(candidate.status == AffordanceStatus.UNSAFE for candidate in constrained.candidates)

    base_caps = create_default_capability_state()
    disabled_caps = CapabilityState(
        capabilities=tuple(
            CapabilitySpec(
                option_class=spec.option_class,
                enabled=False if spec.option_class == AffordanceOptionClass.LOAD_SHEDDING else spec.enabled,
                max_intensity=spec.max_intensity,
                cooldown_steps_remaining=spec.cooldown_steps_remaining,
                risk_multiplier=spec.risk_multiplier,
                source_ref=spec.source_ref,
            )
            for spec in base_caps.capabilities
        ),
        confidence=base_caps.confidence,
    )
    unavailable = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=disabled_caps,
    )
    assert any(candidate.status == AffordanceStatus.UNAVAILABLE for candidate in unavailable.candidates)


def test_regulation_contour_replay_persistence_keeps_load_bearing_state() -> None:
    runtime = _bootstrapped_state()
    sensor = _sensor_unit("regulation persistence", "m-reg-persist")
    regulation_state = _regulation_state(
        sensor.unit.unit_id, energy=23.0, cognitive=86.0, safety=40.0
    )
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    candidate = _first_available(affordances)
    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-persist",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("persist",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                source_ref=sensor.unit.unit_id,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=(sensor.unit.unit_id,)),
    )
    persisted = persist_preference_result_via_f01(
        result=result,
        runtime_state=runtime,
        transition_id="tr-contour-reg-persist",
        requested_at="2026-04-02T00:10:00+00:00",
    )

    assert persisted.accepted is True
    payload = persisted.state.trace.events[-1].payload["preference_snapshot"]
    assert payload["preference_state"]["entries"]
    assert payload["preference_state"]["entries"][0]["option_class_id"] == candidate.option_class.value
    assert payload["preference_state"]["entries"][0]["last_update_provenance"]
    assert payload["telemetry"]["input_affordance_ids"]
    assert payload["telemetry"]["attempted_update_paths"]
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT

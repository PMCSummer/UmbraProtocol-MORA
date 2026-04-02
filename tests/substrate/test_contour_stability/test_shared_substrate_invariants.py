from dataclasses import FrozenInstanceError

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
from substrate.language_surface import build_utterance_surface
from substrate.language_surface.policy import evaluate_surface_downstream_gate
from substrate.morphosyntax import build_morphosyntax_candidate_space, evaluate_morphosyntax_downstream_gate
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    evaluate_preference_downstream_gate,
    update_regulatory_preferences,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-shared-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-shared-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def test_only_f01_mutates_runtime_state_and_direct_mutation_is_blocked() -> None:
    runtime = _bootstrapped_state()
    start_revision = runtime.runtime.revision

    report_unit = ground_epistemic_input(
        InputMaterial(material_id="m-shared-report", content="I feel overloaded"),
        SourceMetadata(
            source_id="user-report",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    assert report_unit.unit.status.value == "report"
    assert report_unit.allowance.can_treat_as_observation is False

    surface = build_utterance_surface(report_unit.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=24.0, source_ref=report_unit.unit.unit_id),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=86.0, source_ref=report_unit.unit.unit_id),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=(report_unit.unit.unit_id,)),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    candidate = affordances.candidates[0]
    preferences = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-shared-1",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("shared",),
                observed_short_term_delta=0.6,
                observed_long_term_delta=0.45,
                attribution_confidence=regulation_state.confidence,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=(report_unit.unit.unit_id,)),
    )

    assert runtime.runtime.revision == start_revision
    assert syntax.hypothesis_set.no_selected_winner is True
    assert preferences.no_final_selection_performed is True

    with pytest.raises(FrozenInstanceError):
        runtime.runtime.revision = runtime.runtime.revision + 1


def test_raw_bypass_rejected_where_typed_seams_are_required() -> None:
    with pytest.raises(TypeError):
        evaluate_surface_downstream_gate("raw-text")
    with pytest.raises(TypeError):
        build_morphosyntax_candidate_space("raw-text")
    with pytest.raises(TypeError):
        evaluate_morphosyntax_downstream_gate("raw")
    with pytest.raises(TypeError):
        evaluate_preference_downstream_gate("raw")


def test_load_bearing_snapshots_are_not_aggregate_only() -> None:
    sensor = ground_epistemic_input(
        InputMaterial(material_id="m-shared-sensor", content="signal stream"),
        SourceMetadata(
            source_id="sensor-shared",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            confidence_hint=ConfidenceLevel.HIGH,
        ),
    )
    surface_result = build_utterance_surface(sensor.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)

    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=22.0, source_ref=sensor.unit.unit_id),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=92.0, source_ref=sensor.unit.unit_id),
            NeedSignal(axis=NeedAxis.SAFETY, value=38.0, source_ref=sensor.unit.unit_id),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=(sensor.unit.unit_id,)),
    ).state
    affordance_result = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    c = affordance_result.candidates[0]
    pref_result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordance_result,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-shared-load",
                option_class_id=c.option_class,
                affordance_id=c.affordance_id,
                target_need_or_set=c.target_axes,
                context_scope=("load-bearing",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.5,
                attribution_confidence=regulation_state.confidence,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=(sensor.unit.unit_id,)),
    )

    surface_payload = surface_result.surface.tokens
    syntax_payload = syntax_result.hypothesis_set.hypotheses[0]
    pref_payload = pref_result.updated_preference_state.entries[0]

    assert surface_payload
    assert syntax_payload.token_features
    assert syntax_payload.unresolved_attachments is not None
    assert pref_payload.last_update_provenance
    assert sensor.unit.unit_id in pref_result.telemetry.source_lineage

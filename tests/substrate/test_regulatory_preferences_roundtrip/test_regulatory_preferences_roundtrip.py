import json

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    persist_preference_result_via_f01,
    preference_result_to_payload,
    update_regulatory_preferences,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-r03-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-r03-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _preference_result():
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=19.0, source_ref="energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=91.0, source_ref="cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=42.0, source_ref="safety"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    candidate = affordances.candidates[0]
    return update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-roundtrip-main",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("roundtrip",),
                observed_short_term_delta=0.68,
                observed_long_term_delta=0.49,
                attribution_confidence=RegulationConfidence.HIGH,
                provenance="roundtrip",
                observed_at_step=1,
            ),
            OutcomeTrace(
                episode_id="ep-roundtrip-blocked",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("roundtrip",),
                observed_short_term_delta=0.2,
                observed_long_term_delta=None,
                attribution_confidence=RegulationConfidence.MEDIUM,
                delayed_window_complete=False,
                provenance="roundtrip",
                observed_at_step=2,
            ),
        ),
    )


def test_snapshot_contains_load_bearing_preference_fields_not_just_aggregates() -> None:
    result = _preference_result()
    payload = preference_result_to_payload(result)

    entry = payload["preference_state"]["entries"][0]
    assert entry["option_class_id"]
    assert entry["preference_sign"]
    assert isinstance(entry["preference_strength"], float)
    assert entry["expected_short_term_delta"] is not None
    assert entry["expected_long_term_delta"] is not None
    assert entry["confidence"]
    assert entry["context_scope"]
    assert entry["time_horizon"]
    assert entry["conflict_state"]
    assert entry["last_update_provenance"]
    assert payload["preference_state"]["unresolved_updates"]
    assert payload["update_events"]


def test_persistence_via_f01_keeps_structural_integrity_and_provenance() -> None:
    runtime_state = _bootstrapped_state()
    result = _preference_result()
    persisted = persist_preference_result_via_f01(
        result=result,
        runtime_state=runtime_state,
        transition_id="tr-r03-roundtrip-persist",
        requested_at="2026-04-02T00:07:00+00:00",
    )
    assert persisted.accepted is True
    snapshot = persisted.state.trace.events[-1].payload["preference_snapshot"]
    entry = snapshot["preference_state"]["entries"][0]

    assert snapshot["preference_state"]["entries"]
    assert snapshot["preference_state"]["unresolved_updates"]
    assert snapshot["update_events"]
    assert snapshot["telemetry"]["updated_entry_ids"]
    assert snapshot["telemetry"]["attempted_update_paths"]
    assert entry["preference_sign"]
    assert entry["preference_strength"] >= 0.0
    assert "episode:ep-roundtrip-main" in entry["last_update_provenance"]

    as_json = json.loads(json.dumps(snapshot))
    assert as_json["preference_state"]["entries"][0]["option_class_id"]
    assert as_json["telemetry"]["processed_episode_ids"]

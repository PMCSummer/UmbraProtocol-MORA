import json

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.state import create_empty_state
from substrate.transition import execute_transition
from substrate.viability_control import (
    ViabilityContext,
    compute_viability_control_state,
    persist_viability_control_result_via_f01,
    viability_result_to_payload,
)


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-r04-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-r04-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _result(*, energy: float, cognitive: float, safety: float):
    regulation = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-round-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-round-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-round-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-roundtrip",)),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation,
        capability_state=create_default_capability_state(),
    )
    return compute_viability_control_state(regulation, affordances, create_empty_preference_state())


def test_viability_snapshot_keeps_load_bearing_state_not_only_aggregates() -> None:
    result = _result(energy=17.0, cognitive=91.0, safety=38.0)
    payload = viability_result_to_payload(result)

    assert payload["state"]["pressure_level"] >= 0.0
    assert payload["state"]["escalation_stage"]
    assert payload["state"]["override_scope"]
    assert payload["state"]["persistence_state"]
    assert payload["state"]["uncertainty_state"] is not None
    assert payload["directives"] is not None
    assert payload["telemetry"]["computed_pressure_level"] >= 0.0
    assert payload["telemetry"]["attempted_computation_paths"]
    assert payload["telemetry"]["downstream_gate"]["restrictions"] is not None


def test_persist_reconstruct_continue_keeps_viability_structure() -> None:
    runtime = _bootstrapped_state()
    first = _result(energy=16.0, cognitive=93.0, safety=36.0)
    persisted = persist_viability_control_result_via_f01(
        result=first,
        runtime_state=runtime,
        transition_id="tr-r04-roundtrip-first",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    snapshot = persisted.state.trace.events[-1].payload["viability_control_snapshot"]
    assert snapshot["state"]["escalation_stage"]
    assert snapshot["state"]["input_regulation_snapshot_ref"]
    assert snapshot["telemetry"]["boundary_compatibility"] is not None
    json.loads(json.dumps(snapshot))

    regulation_second = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=18.0, source_ref="r04-round-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=89.0, source_ref="r04-round-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=42.0, source_ref="r04-round-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-roundtrip",)),
    ).state
    affordances_second = generate_regulation_affordances(
        regulation_state=regulation_second,
        capability_state=create_default_capability_state(),
    )
    continued = compute_viability_control_state(
        regulation_second,
        affordances_second,
        create_empty_preference_state(),
        context=ViabilityContext(prior_viability_state=first.state),
    )
    assert continued.state.deescalation_conditions

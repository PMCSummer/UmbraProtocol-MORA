import pytest

from substrate.affordances import (
    AffordanceContext,
    AffordanceStatus,
    affordance_result_to_payload,
    create_default_capability_state,
    evaluate_affordance_landscape_for_downstream,
    generate_regulation_affordances,
    persist_affordance_result_via_f01,
)
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _regulation_state_for_downstream():
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=20.0, source_ref="energy-low"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=85.0, source_ref="cog-high"),
            NeedSignal(axis=NeedAxis.SAFETY, value=45.0, source_ref="safety-low"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r01",)),
    ).state


def test_r02_returns_landscape_not_hidden_selected_winner() -> None:
    result = generate_regulation_affordances(
        regulation_state=_regulation_state_for_downstream(),
        capability_state=create_default_capability_state(),
    )

    assert len(result.candidates) >= 2
    assert result.summary.no_selection_performed is True
    assert not hasattr(result, "selected_affordance")


def test_downstream_contract_requires_typed_affordances_and_changes_with_landscape() -> None:
    result = generate_regulation_affordances(
        regulation_state=_regulation_state_for_downstream(),
        capability_state=create_default_capability_state(),
    )
    gate = evaluate_affordance_landscape_for_downstream(
        result.candidates, require_available=True
    )
    assert gate.accepted_candidate_ids
    with pytest.raises(TypeError):
        evaluate_affordance_landscape_for_downstream(["label-only"], require_available=True)

    weaker_state = update_regulation_state(
        signals=(),
        prior_state=None,
        context=RegulationContext(),
    ).state
    weaker_result = generate_regulation_affordances(
        regulation_state=weaker_state,
        capability_state=create_default_capability_state(),
        context=AffordanceContext(require_available_candidates=True),
    )
    assert gate.accepted_candidate_ids != weaker_result.gate.accepted_candidate_ids


def test_policy_surface_is_load_bearing_for_restrictions() -> None:
    result = generate_regulation_affordances(
        regulation_state=_regulation_state_for_downstream(),
        capability_state=create_default_capability_state(),
        context=AffordanceContext(max_risk_tolerance=0.2, require_available_candidates=True),
    )
    gate = evaluate_affordance_landscape_for_downstream(
        result.candidates, require_available=True
    )
    assert "unsafe_present" in gate.restrictions

    naive_top = max(
        result.candidates, key=lambda candidate: candidate.expected_effect.effect_strength_estimate
    )
    assert naive_top.status in {AffordanceStatus.UNSAFE, AffordanceStatus.PROVISIONAL}
    assert naive_top.affordance_id not in gate.accepted_candidate_ids


def test_boundary_non_overreach_no_semantics_world_claims_or_action_selection() -> None:
    result = generate_regulation_affordances(
        regulation_state=_regulation_state_for_downstream(),
        capability_state=create_default_capability_state(),
    )
    assert not hasattr(result, "world_truth")
    assert not hasattr(result, "intent")
    assert not hasattr(result, "action_plan")


def test_persistence_handoff_uses_f01_transition_route_only() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-r02-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-01T00:00:00+00:00",
            event_id="ev-r02-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    result = generate_regulation_affordances(
        regulation_state=_regulation_state_for_downstream(),
        capability_state=create_default_capability_state(),
    )
    persisted = persist_affordance_result_via_f01(
        result=result,
        runtime_state=boot.state,
        transition_id="tr-r02-persist",
        requested_at="2026-04-01T00:20:00+00:00",
    )

    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert "affordance_snapshot" in persisted.state.trace.events[-1].payload
    assert affordance_result_to_payload(result)["summary"]["total_candidates"] == len(
        result.candidates
    )


def test_ablation_lite_without_r02_only_pressure_no_candidate_landscape() -> None:
    regulation_state = _regulation_state_for_downstream()
    without_r02_surface = {
        need.axis.value: need.pressure for need in regulation_state.needs
    }
    with_r02 = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )

    assert without_r02_surface
    assert "candidates" not in without_r02_surface
    assert with_r02.summary.total_candidates > 0
    assert with_r02.gate.accepted_candidate_ids is not None

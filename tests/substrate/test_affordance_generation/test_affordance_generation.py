from substrate.affordances import (
    AffordanceStatus,
    create_default_capability_state,
    generate_regulation_affordances,
)
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state


def _r01_state_for_generation():
    regulation = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=20.0, source_ref="energy-low"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=95.0, source_ref="cog-high"),
            NeedSignal(axis=NeedAxis.SAFETY, value=20.0, source_ref="safety-low"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r01-source",)),
    )
    return regulation.state


def test_generation_produces_structured_affordance_candidates() -> None:
    result = generate_regulation_affordances(
        regulation_state=_r01_state_for_generation(),
        capability_state=create_default_capability_state(),
    )

    assert result.candidates
    assert result.summary.total_candidates == len(result.candidates)
    for candidate in result.candidates:
        assert candidate.affordance_id
        assert candidate.option_class.value
        assert candidate.target_axes
        assert candidate.status in set(AffordanceStatus)
        assert candidate.expected_effect.effect_strength_estimate >= 0.0
        assert candidate.cost.basis
        assert candidate.risk.level >= 0.0
        assert candidate.latency_steps >= 0
        assert candidate.duration_steps > 0
        assert candidate.applicability is not None
        assert candidate.tradeoff is not None
        assert candidate.provenance_basis


def test_generation_emits_typed_telemetry_and_gate_surface() -> None:
    result = generate_regulation_affordances(
        regulation_state=_r01_state_for_generation(),
        capability_state=create_default_capability_state(),
    )

    assert result.telemetry.generated_candidate_ids
    assert result.telemetry.candidate_statuses
    assert result.telemetry.expected_effects
    assert result.telemetry.cost_risk_surface
    assert result.telemetry.downstream_gate.accepted_candidate_ids is not None
    assert len({candidate.expected_effect.effect_class for candidate in result.candidates}) >= 2

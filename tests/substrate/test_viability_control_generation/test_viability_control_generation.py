from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    update_regulatory_preferences,
)
from substrate.viability_control import (
    ViabilityControlResult,
    ViabilityEscalationStage,
    compute_viability_control_state,
)


def _upstream_bundle():
    regulation_result = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=18.0, source_ref="r04-gen-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=92.0, source_ref="r04-gen-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=40.0, source_ref="r04-gen-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-generation",)),
    )
    affordances = generate_regulation_affordances(
        regulation_state=regulation_result.state,
        capability_state=create_default_capability_state(),
    )
    candidate = next(
        (item for item in affordances.candidates if item.status.value == "available"),
        affordances.candidates[0],
    )
    preference_result = update_regulatory_preferences(
        regulation_state=regulation_result.state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-r04-gen",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("r04", "generation"),
                observed_short_term_delta=0.65,
                observed_long_term_delta=0.45,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=("r04-generation",)),
    )
    return regulation_result, affordances, preference_result


def test_r04_generates_distinct_typed_viability_control_state() -> None:
    regulation_result, affordances, preference_result = _upstream_bundle()
    result = compute_viability_control_state(
        regulation_result,
        affordances,
        preference_result,
    )

    assert isinstance(result, ViabilityControlResult)
    assert result.no_action_selection_performed is True
    assert result.state.input_regulation_snapshot_ref.startswith("regulation-step-")
    assert result.state.input_affordance_ref.startswith("affordance-candidates:")
    assert result.state.input_preference_ref.startswith("preference-step-")
    assert result.state.pressure_level >= 0.0
    assert result.state.escalation_stage in {
        ViabilityEscalationStage.ELEVATED,
        ViabilityEscalationStage.THREAT,
        ViabilityEscalationStage.CRITICAL,
    }
    assert result.directives
    assert result.telemetry.computed_pressure_level == result.state.pressure_level
    assert result.telemetry.affected_need_ids == result.state.affected_need_ids
    assert result.telemetry.attempted_computation_paths

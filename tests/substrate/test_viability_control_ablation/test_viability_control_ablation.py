from dataclasses import replace

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import (
    ViabilityCalibrationSpec,
    ViabilityContext,
    ViabilityDirectiveType,
    ViabilityOverrideScope,
    compute_viability_control_state,
    evaluate_viability_downstream_gate,
    create_default_viability_calibration_spec,
)


def _regulation(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-abl-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-abl-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-abl-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-ablation",)),
    ).state


def _dummy_consumer(result, tasks):
    gate = evaluate_viability_downstream_gate(result)
    accepted = [
        directive
        for directive in result.directives
        if directive.directive_id in gate.accepted_directive_ids
    ]
    reduction = 0.0
    for directive in accepted:
        if directive.directive_type != ViabilityDirectiveType.TASK_PERMISSIVENESS_REDUCTION:
            continue
        if directive.override_scope == ViabilityOverrideScope.EMERGENCY:
            reduction = max(reduction, min(1.0, directive.intensity))
        elif directive.override_scope == ViabilityOverrideScope.BROAD:
            reduction = max(reduction, min(0.9, directive.intensity))
        elif directive.override_scope == ViabilityOverrideScope.FOCUSED:
            reduction = max(reduction, min(0.7, directive.intensity))
        elif directive.override_scope == ViabilityOverrideScope.NARROW:
            reduction = max(reduction, min(0.5, directive.intensity))
    if reduction <= 0.0:
        return tasks
    return tuple(
        task for task in tasks if task["kind"] == "viability" or task["priority"] >= (1.0 - reduction)
    )


def test_ablation_of_override_scope_weakens_downstream_permissiveness_effect() -> None:
    state = _regulation(energy=14.0, cognitive=95.0, safety=35.0)
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    result = compute_viability_control_state(state, affordances, create_empty_preference_state())
    tasks = (
        {"task_id": "viability-1", "kind": "viability", "priority": 0.25},
        {"task_id": "routine-1", "kind": "routine", "priority": 0.35},
        {"task_id": "routine-2", "kind": "routine", "priority": 0.55},
    )
    with_scope = _dummy_consumer(result, tasks)
    ablated = replace(
        result,
        directives=tuple(
            replace(directive, override_scope=ViabilityOverrideScope.NONE)
            for directive in result.directives
        ),
    )
    without_scope = _dummy_consumer(ablated, tasks)
    assert len(with_scope) <= len(without_scope)


def test_persistence_component_is_load_bearing_under_repeated_failed_recovery() -> None:
    state = _regulation(energy=34.0, cognitive=76.0, safety=50.0)
    prior = _regulation(energy=36.0, cognitive=74.0, safety=52.0)
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    default = compute_viability_control_state(
        state,
        affordances,
        create_empty_preference_state(),
        context=ViabilityContext(
            prior_regulation_state=prior,
            recent_failed_recovery_attempts=3,
        ),
    )
    persistence_ablated = ViabilityCalibrationSpec(
        calibration_id="r04-ablate-persistence",
        persistence_weight=0.0,
        failed_recovery_weight=0.0,
        max_persistence_component=0.0,
        max_failed_component=0.0,
    )
    ablated = compute_viability_control_state(
        state,
        affordances,
        create_empty_preference_state(),
        context=ViabilityContext(
            prior_regulation_state=prior,
            recent_failed_recovery_attempts=3,
        ),
        calibration_spec=persistence_ablated,
    )
    assert default.state.pressure_level > ablated.state.pressure_level


def test_strict_recoverability_evidence_threshold_forces_no_strong_override_claim() -> None:
    state = _regulation(energy=18.0, cognitive=89.0, safety=42.0)
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    base = compute_viability_control_state(state, affordances, create_empty_preference_state())
    strict = compute_viability_control_state(
        state,
        affordances,
        create_empty_preference_state(),
        calibration_spec=replace(
            create_default_viability_calibration_spec(),
            min_recoverability_evidence_quality=0.95,
            strong_override_min_recoverability_evidence=0.95,
        ),
    )
    assert strict.state.no_strong_override_claim is True
    assert strict.state.recoverability_estimate is None
    assert base.state.escalation_stage == strict.state.escalation_stage

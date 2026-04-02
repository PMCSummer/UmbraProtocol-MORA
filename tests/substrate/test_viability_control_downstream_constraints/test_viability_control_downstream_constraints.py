from dataclasses import replace

import pytest

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import (
    ViabilityDirectiveType,
    ViabilityGateDecision,
    compute_viability_control_state,
    evaluate_viability_downstream_gate,
)


def _typed_result():
    regulation = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=14.0, source_ref="r04-down-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=95.0, source_ref="r04-down-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=36.0, source_ref="r04-down-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-downstream",)),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation,
        capability_state=create_default_capability_state(),
    )
    return compute_viability_control_state(
        regulation,
        affordances,
        create_empty_preference_state(),
    )


def _dummy_consumer(result, tasks):
    gate = evaluate_viability_downstream_gate(result)
    accepted_directives = [
        directive
        for directive in result.directives
        if directive.directive_id in gate.accepted_directive_ids
    ]
    reduction = max(
        (
            directive.intensity
            for directive in accepted_directives
            if directive.directive_type == ViabilityDirectiveType.TASK_PERMISSIVENESS_REDUCTION
        ),
        default=0.0,
    )
    interrupt = any(
        directive.directive_type == ViabilityDirectiveType.INTERRUPT_RECOMMENDATION
        for directive in accepted_directives
    )
    protective = any(
        directive.directive_type == ViabilityDirectiveType.PROTECTIVE_MODE_REQUEST
        for directive in accepted_directives
    )
    if reduction <= 0.0:
        allowed = tasks
    else:
        allowed = tuple(
            task for task in tasks if task["kind"] == "viability" or task["priority"] >= (1.0 - reduction)
        )
    return {
        "allowed_tasks": allowed,
        "interrupt": interrupt,
        "protective_mode": protective,
        "gate": gate,
    }


def test_downstream_gate_rejects_raw_and_accepts_typed_artifacts() -> None:
    with pytest.raises(TypeError):
        evaluate_viability_downstream_gate("raw")
    with pytest.raises(TypeError):
        evaluate_viability_downstream_gate({"pressure": 0.9})

    result = _typed_result()
    gate_from_result = evaluate_viability_downstream_gate(result)
    gate_from_state = evaluate_viability_downstream_gate(result.state)
    assert isinstance(gate_from_result, ViabilityGateDecision)
    assert gate_from_result.restrictions
    assert "no_action_selection_performed" in gate_from_result.restrictions
    assert gate_from_state.restrictions


def test_dummy_downstream_obeys_typed_viability_directives_and_ablation_degrades_effect() -> None:
    result = _typed_result()
    tasks = (
        {"task_id": "task-viability-1", "kind": "viability", "priority": 0.4},
        {"task_id": "task-routine-1", "kind": "routine", "priority": 0.3},
        {"task_id": "task-routine-2", "kind": "routine", "priority": 0.5},
    )
    with_viability = _dummy_consumer(result, tasks)

    ablated = replace(
        result,
        directives=(),
    )
    without_viability = _dummy_consumer(ablated, tasks)

    assert len(with_viability["allowed_tasks"]) <= len(without_viability["allowed_tasks"])
    assert with_viability["allowed_tasks"] != without_viability["allowed_tasks"] or with_viability["interrupt"] != without_viability["interrupt"]

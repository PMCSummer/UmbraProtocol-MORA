from __future__ import annotations

from substrate.viability_control.models import (
    ViabilityControlResult,
    ViabilityControlState,
    ViabilityDirectiveType,
    ViabilityGateDecision,
)


def evaluate_viability_downstream_gate(
    viability_result_or_state: object,
) -> ViabilityGateDecision:
    if isinstance(viability_result_or_state, ViabilityControlResult):
        state = viability_result_or_state.state
        directives = viability_result_or_state.directives
    elif isinstance(viability_result_or_state, ViabilityControlState):
        state = viability_result_or_state
        directives = ()
    else:
        raise TypeError(
            "viability downstream gate requires typed ViabilityControlResult/ViabilityControlState"
        )

    restrictions: list[str] = ["no_action_selection_performed"]
    accepted_directive_ids: list[str] = []
    rejected_directive_ids: list[str] = []

    if state.uncertainty_state:
        restrictions.extend(marker.value for marker in state.uncertainty_state)
    if state.no_strong_override_claim:
        restrictions.append("override_capped_by_uncertainty")

    for directive in directives:
        if state.no_strong_override_claim and directive.directive_type in {
            ViabilityDirectiveType.INTERRUPT_RECOMMENDATION,
            ViabilityDirectiveType.PROTECTIVE_MODE_REQUEST,
        }:
            rejected_directive_ids.append(directive.directive_id)
            continue
        if directive.intensity < 0.2:
            rejected_directive_ids.append(directive.directive_id)
            restrictions.append("weak_directive_present")
            continue
        accepted_directive_ids.append(directive.directive_id)

    accepted = bool(accepted_directive_ids)
    if accepted:
        reason = "typed viability directives available with bounded override restrictions"
    else:
        reason = "no downstream-safe viability directives under current uncertainty/stage"
        restrictions.append("no_viability_directives")

    return ViabilityGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_directive_ids=tuple(accepted_directive_ids),
        rejected_directive_ids=tuple(dict.fromkeys(rejected_directive_ids)),
        state_ref=state.input_regulation_snapshot_ref,
    )

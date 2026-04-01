from __future__ import annotations

from dataclasses import dataclass

from substrate.regulation.models import (
    NeedAxis,
    RegulationBias,
    RegulationConfidence,
    RegulationContext,
    RegulationState,
    TradeoffState,
)


@dataclass(frozen=True, slots=True)
class RegulationGateDecision:
    allowed: bool
    reason: str
    applied_restrictions: tuple[str, ...]


def derive_regulation_bias(
    state: RegulationState,
    tradeoff: TradeoffState,
    context: RegulationContext,
) -> RegulationBias:
    if not isinstance(state, RegulationState):
        raise TypeError("regulation bias requires RegulationState")

    urgency_values: list[tuple[NeedAxis, float]] = []
    for need in state.needs:
        urgency = round(
            need.pressure + (need.deviation * 0.5) + (need.unresolved_steps * 1.25), 4
        )
        urgency_values.append((need.axis, urgency))

    restrictions: list[str] = []
    claim_strength = "moderate"
    reason = "regulation bias derived from structured need pressures"

    if state.confidence == RegulationConfidence.LOW:
        urgency_values = [(axis, round(value * 0.7, 4)) for axis, value in urgency_values]
        restrictions.append("low_confidence")
        claim_strength = "weak"
        reason = "low confidence limits urgency strength"
    elif state.confidence == RegulationConfidence.MEDIUM:
        claim_strength = "guarded"

    if state.partial_known is not None:
        restrictions.append("partial_known")
    if state.abstention is not None:
        restrictions.append("abstain")
        claim_strength = "abstain"
        reason = state.abstention.reason

    salience_order = tuple(
        axis for axis, _ in sorted(urgency_values, key=lambda item: item[1], reverse=True)
    )
    dominant = tradeoff.dominant_axis
    coping_mode = _coping_mode_for_axis(dominant)

    if context.require_strong_claim and claim_strength != "strong":
        restrictions.append("strong_claim_not_supported")
    if (
        context.require_strong_claim
        and state.confidence == RegulationConfidence.HIGH
        and state.abstention is None
        and dominant is not None
    ):
        claim_strength = "strong"

    return RegulationBias(
        urgency_by_axis=tuple(urgency_values),
        salience_order=salience_order,
        coping_mode=coping_mode,
        claim_strength=claim_strength,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
    )


def evaluate_downstream_regulation_gate(
    bias: RegulationBias,
    *,
    require_strong_claim: bool,
) -> RegulationGateDecision:
    if not isinstance(bias, RegulationBias):
        raise TypeError("downstream regulation gate requires RegulationBias")

    restrictions = list(bias.restrictions)
    if "abstain" in restrictions:
        return RegulationGateDecision(
            allowed=False,
            reason="regulation bias requests abstention",
            applied_restrictions=tuple(dict.fromkeys(restrictions)),
        )
    if require_strong_claim and bias.claim_strength != "strong":
        restrictions.append("strong_claim_required")
        return RegulationGateDecision(
            allowed=False,
            reason="strong claim requested but regulation bias is not strong",
            applied_restrictions=tuple(dict.fromkeys(restrictions)),
        )
    return RegulationGateDecision(
        allowed=True,
        reason="downstream gate allows use under current regulation bias",
        applied_restrictions=tuple(dict.fromkeys(restrictions)),
    )


def _coping_mode_for_axis(axis: NeedAxis | None) -> str:
    if axis is None:
        return "stabilize"
    if axis == NeedAxis.ENERGY:
        return "conserve_resources"
    if axis == NeedAxis.COGNITIVE_LOAD:
        return "reduce_cognitive_load"
    if axis == NeedAxis.SAFETY:
        return "protective_guard"
    if axis == NeedAxis.SOCIAL_CONTACT:
        return "rebalance_social_contact"
    if axis == NeedAxis.NOVELTY:
        return "rebalance_exploration"
    return "stabilize"

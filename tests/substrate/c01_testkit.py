from __future__ import annotations

from dataclasses import dataclass

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    update_regulatory_preferences,
)
from substrate.viability_control import ViabilityContext, compute_viability_control_state


@dataclass(frozen=True, slots=True)
class C01UpstreamBundle:
    regulation: object
    affordances: object
    preferences: object
    viability: object


def build_c01_upstream(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool = False,
    prior_regulation_state: object | None = None,
    prior_viability_state: object | None = None,
) -> C01UpstreamBundle:
    regulation = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref=f"c01-{case_id}-energy"),
            NeedSignal(
                axis=NeedAxis.COGNITIVE_LOAD,
                value=cognitive,
                source_ref=f"c01-{case_id}-cognitive",
            ),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref=f"c01-{case_id}-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=(f"c01-{case_id}",)),
    )
    affordances = generate_regulation_affordances(
        regulation_state=regulation.state,
        capability_state=create_default_capability_state(),
    )
    candidate = next(
        (item for item in affordances.candidates if item.status.value == "available"),
        affordances.candidates[0],
    )
    if unresolved_preference:
        short_delta = 0.35
        long_delta = None
        delayed_window_complete = False
    else:
        short_delta = 0.55
        long_delta = 0.3
        delayed_window_complete = True
    preferences = update_regulatory_preferences(
        regulation_state=regulation.state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id=f"ep-c01-{case_id}",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("c01", case_id),
                observed_short_term_delta=short_delta,
                observed_long_term_delta=long_delta,
                attribution_confidence=RegulationConfidence.HIGH,
                delayed_window_complete=delayed_window_complete,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=(f"c01-{case_id}",)),
    )
    viability = compute_viability_control_state(
        regulation,
        affordances,
        preferences,
        context=ViabilityContext(
            source_lineage=(f"c01-{case_id}",),
            prior_regulation_state=prior_regulation_state,
            prior_viability_state=prior_viability_state,
        ),
    )
    return C01UpstreamBundle(
        regulation=regulation,
        affordances=affordances,
        preferences=preferences,
        viability=viability,
    )

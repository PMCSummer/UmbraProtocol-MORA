from __future__ import annotations

from substrate.affordances.models import (
    AffordanceGateDecision,
    AffordanceStatus,
    RegulationAffordance,
)


def evaluate_affordance_landscape_for_downstream(
    candidates: tuple[RegulationAffordance, ...] | list[RegulationAffordance],
    *,
    require_available: bool,
) -> AffordanceGateDecision:
    if not isinstance(candidates, (tuple, list)):
        raise TypeError(
            "downstream affordance gate requires typed RegulationAffordance candidates"
        )
    typed_candidates: list[RegulationAffordance] = []
    for candidate in candidates:
        if not isinstance(candidate, RegulationAffordance):
            raise TypeError(
                "downstream affordance gate requires typed RegulationAffordance candidates"
            )
        typed_candidates.append(candidate)

    accepted: list[RegulationAffordance] = [
        candidate
        for candidate in typed_candidates
        if candidate.status == AffordanceStatus.AVAILABLE
    ]
    restrictions: list[str] = []

    if require_available and not accepted:
        restrictions.append("no_available_affordance")
    if not require_available and not accepted:
        accepted = [
            candidate
            for candidate in typed_candidates
            if candidate.status == AffordanceStatus.PROVISIONAL
        ]
        if accepted:
            restrictions.append("provisional_only")

    rejected_ids = tuple(
        candidate.affordance_id
        for candidate in typed_candidates
        if candidate not in accepted
    )
    accepted_ids = tuple(candidate.affordance_id for candidate in accepted)

    status_restrictions = {
        AffordanceStatus.BLOCKED: "blocked_present",
        AffordanceStatus.UNAVAILABLE: "unavailable_present",
        AffordanceStatus.UNSAFE: "unsafe_present",
        AffordanceStatus.PROVISIONAL: "provisional_present",
    }
    for candidate in typed_candidates:
        if candidate.status in status_restrictions:
            restrictions.append(status_restrictions[candidate.status])

    hints = tuple(
        f"focus:{candidate.option_class.value}"
        for candidate in sorted(
            accepted,
            key=lambda item: item.expected_effect.effect_strength_estimate,
            reverse=True,
        )
    )
    if accepted_ids:
        reason = "candidate landscape provided without selecting single winner"
    else:
        reason = "no acceptable affordance candidates under current constraints"
    return AffordanceGateDecision(
        accepted_candidate_ids=accepted_ids,
        rejected_candidate_ids=rejected_ids,
        restrictions=tuple(dict.fromkeys(restrictions)),
        bias_hints=hints,
        reason=reason,
    )

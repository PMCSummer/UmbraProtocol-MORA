from __future__ import annotations

from substrate.morphosyntax.models import SyntaxDownstreamGateDecision, SyntaxHypothesisSet


def evaluate_morphosyntax_downstream_gate(
    hypothesis_set_or_other: object,
) -> SyntaxDownstreamGateDecision:
    if not isinstance(hypothesis_set_or_other, SyntaxHypothesisSet):
        raise TypeError(
            "morphosyntax downstream gate requires typed SyntaxHypothesisSet input"
        )

    hypothesis_set = hypothesis_set_or_other
    restrictions: list[str] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    if hypothesis_set.ambiguity_present:
        restrictions.append("ambiguity_present")
    if len(hypothesis_set.hypotheses) > 1:
        restrictions.append("multi_candidate_space")
    if hypothesis_set.no_selected_winner:
        restrictions.append("no_selected_winner")

    for hypothesis in hypothesis_set.hypotheses:
        if hypothesis.unresolved_attachments:
            restrictions.append("unresolved_attachment_present")
        if hypothesis.confidence < 0.6:
            restrictions.append("low_confidence_hypothesis")
        if not hypothesis.edges:
            restrictions.append("shallow_structure_only")
        if hypothesis.confidence >= 0.2:
            accepted_ids.append(hypothesis.hypothesis_id)
        else:
            rejected_ids.append(hypothesis.hypothesis_id)

    accepted = bool(hypothesis_set.hypotheses)
    if accepted:
        reason = "typed morphosyntax candidate space exposed for downstream use"
    else:
        reason = "empty morphosyntax candidate space"

    return SyntaxDownstreamGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_hypothesis_ids=tuple(accepted_ids),
        rejected_hypothesis_ids=tuple(rejected_ids),
        hypothesis_set_ref=hypothesis_set.source_surface_ref,
    )

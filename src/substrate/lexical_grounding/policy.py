from __future__ import annotations

from substrate.lexical_grounding.models import (
    LexicalGroundingBundle,
    LexicalGroundingGateDecision,
    LexicalGroundingResult,
)


def evaluate_lexical_grounding_downstream_gate(
    lexical_grounding_result_or_bundle: object,
) -> LexicalGroundingGateDecision:
    if isinstance(lexical_grounding_result_or_bundle, LexicalGroundingResult):
        bundle = lexical_grounding_result_or_bundle.bundle
    elif isinstance(lexical_grounding_result_or_bundle, LexicalGroundingBundle):
        bundle = lexical_grounding_result_or_bundle
    else:
        raise TypeError(
            "lexical grounding gate requires typed LexicalGroundingResult/LexicalGroundingBundle"
        )

    restrictions: list[str] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    if bundle.no_final_resolution_performed:
        restrictions.append("no_final_resolution_performed")
    if bundle.unknown_states:
        restrictions.append("unknown_grounding_present")
    if bundle.conflicts:
        restrictions.append("grounding_conflict_present")
    if bundle.syntax_instability_present:
        restrictions.append("syntax_instability_present")
    if any(hypothesis.unresolved for hypothesis in bundle.reference_hypotheses):
        restrictions.append("unresolved_reference_present")
    if bundle.ambiguity_reasons:
        restrictions.append("ambiguity_present")

    for candidate in bundle.lexeme_candidates:
        if candidate.confidence >= 0.2:
            accepted_ids.append(candidate.candidate_id)
        else:
            rejected_ids.append(candidate.candidate_id)
    for hypothesis in bundle.reference_hypotheses:
        if hypothesis.confidence >= 0.2:
            accepted_ids.append(hypothesis.reference_id)
        else:
            rejected_ids.append(hypothesis.reference_id)
    for deixis in bundle.deixis_candidates:
        if deixis.confidence >= 0.2:
            accepted_ids.append(deixis.candidate_id)
        else:
            rejected_ids.append(deixis.candidate_id)

    accepted = bool(bundle.mention_anchors)
    if not accepted:
        restrictions.append("no_mentions")
        reason = "lexical grounding bundle has no mention anchors"
    else:
        reason = "typed lexical grounding candidates exposed with bounded restrictions"

    return LexicalGroundingGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_candidate_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_candidate_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_syntax_ref,
    )

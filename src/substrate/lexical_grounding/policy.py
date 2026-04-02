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
    if bundle.lexicon_primary_used:
        restrictions.append("lexicon_primary_used")
    if bundle.heuristic_fallback_used:
        restrictions.append("heuristic_fallback_used")
    if bundle.no_strong_lexical_claim_from_fallback:
        restrictions.append("no_strong_lexical_claim_from_fallback")
    if bundle.lexicon_handoff_missing:
        restrictions.append("lexicon_handoff_missing")
    if bundle.lexical_basis_degraded:
        restrictions.append("lexical_basis_degraded")
    if bundle.no_strong_lexical_claim_without_lexicon:
        restrictions.append("no_strong_lexical_claim_without_lexicon")
    if any(basis.basis_class.value == "lexicon_capped_unknown" for basis in bundle.lexical_basis_records):
        restrictions.append("lexicon_capped_unknown_basis_present")
    if any(basis.basis_class.value == "no_usable_lexical_basis" for basis in bundle.lexical_basis_records):
        restrictions.append("no_usable_lexical_basis_present")
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

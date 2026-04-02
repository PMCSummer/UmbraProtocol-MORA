from __future__ import annotations

from substrate.dictum_candidates.models import (
    DictumCandidateBundle,
    DictumCandidateResult,
    DictumGateDecision,
)


def evaluate_dictum_downstream_gate(
    dictum_result_or_bundle: object,
) -> DictumGateDecision:
    if isinstance(dictum_result_or_bundle, DictumCandidateResult):
        bundle = dictum_result_or_bundle.bundle
    elif isinstance(dictum_result_or_bundle, DictumCandidateBundle):
        bundle = dictum_result_or_bundle
    else:
        raise TypeError(
            "dictum gate requires typed DictumCandidateResult/DictumCandidateBundle"
        )

    restrictions: list[str] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    if bundle.no_final_resolution_performed:
        restrictions.append("no_final_resolution_performed")
    if bundle.unknowns:
        restrictions.append("dictum_unknown_present")
    if bundle.conflicts:
        restrictions.append("dictum_conflict_present")
    if any(candidate.underspecified_slots for candidate in bundle.dictum_candidates):
        restrictions.append("underspecified_slots_present")
    if any(marker.ambiguous for candidate in bundle.dictum_candidates for marker in candidate.scope_markers):
        restrictions.append("scope_ambiguity_present")
    if any(candidate.quotation_sensitive for candidate in bundle.dictum_candidates):
        restrictions.append("quotation_sensitive_content_present")

    for candidate in bundle.dictum_candidates:
        if candidate.confidence >= 0.2:
            accepted_ids.append(candidate.dictum_candidate_id)
        else:
            rejected_ids.append(candidate.dictum_candidate_id)

    accepted = bool(bundle.dictum_candidates)
    if not accepted:
        restrictions.append("no_dictum_candidates")
        reason = "dictum candidate bundle has no proposition skeletons"
    else:
        reason = "typed dictum candidates exposed with bounded uncertainty restrictions"

    return DictumGateDecision(
        accepted=accepted,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_candidate_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_candidate_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_lexical_grounding_ref,
    )

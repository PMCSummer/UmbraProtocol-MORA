from __future__ import annotations

from substrate.runtime_semantic_graph.models import (
    GraphUsabilityClass,
    RuntimeGraphBundle,
    RuntimeGraphGateDecision,
    RuntimeGraphResult,
)


def evaluate_runtime_graph_downstream_gate(
    runtime_graph_result_or_bundle: object,
) -> RuntimeGraphGateDecision:
    if isinstance(runtime_graph_result_or_bundle, RuntimeGraphResult):
        bundle = runtime_graph_result_or_bundle.bundle
    elif isinstance(runtime_graph_result_or_bundle, RuntimeGraphBundle):
        bundle = runtime_graph_result_or_bundle
    else:
        raise TypeError(
            "runtime graph gate requires typed RuntimeGraphResult/RuntimeGraphBundle"
        )

    restrictions: list[str] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    if bundle.no_final_semantic_closure:
        restrictions.append("no_final_semantic_closure")
    if bundle.low_coverage_mode:
        restrictions.append("low_semantic_coverage")
    if bundle.unresolved_role_slots:
        restrictions.append("unresolved_role_slots_present")
    if bundle.graph_alternatives or bundle.ambiguity_reasons:
        restrictions.append("ambiguity_preserved")
    if any(candidate.unresolved for candidate in bundle.proposition_candidates):
        restrictions.append("incomplete_proposition_candidates")
    if any("source" in alt.reason.lower() for alt in bundle.graph_alternatives):
        restrictions.append("source_scope_uncertain")

    for candidate in bundle.proposition_candidates:
        if candidate.confidence >= 0.2:
            accepted_ids.append(candidate.proposition_id)
        else:
            rejected_ids.append(candidate.proposition_id)

    accepted = bool(bundle.semantic_units and bundle.proposition_candidates)
    if not accepted:
        restrictions.append("no_usable_runtime_graph")
        reason = "runtime semantic graph has no usable proposition candidates"
        usability_class = GraphUsabilityClass.BLOCKED
    else:
        reason = "typed runtime graph emitted with bounded semantic restrictions"
        usability_class = GraphUsabilityClass.USABLE_BOUNDED

    degraded = (
        bundle.low_coverage_mode
        or bool(bundle.unresolved_role_slots)
        or bool(bundle.graph_alternatives)
    )
    if degraded:
        restrictions.append("downstream_authority_degraded")
        if accepted:
            usability_class = GraphUsabilityClass.DEGRADED_BOUNDED

    return RuntimeGraphGateDecision(
        accepted=accepted,
        usability_class=usability_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_proposition_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_proposition_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_grounded_ref,
    )

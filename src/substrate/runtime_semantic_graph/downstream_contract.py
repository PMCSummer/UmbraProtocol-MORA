from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from substrate.runtime_semantic_graph.models import (
    CertaintyClass,
    GraphUsabilityClass,
    PolarityClass,
    RuntimeGraphBundle,
    RuntimeGraphResult,
)
from substrate.runtime_semantic_graph.policy import evaluate_runtime_graph_downstream_gate


class RuntimeSourceMode(str, Enum):
    ASSERTED = "asserted"
    QUOTED = "quoted"
    REPORTED = "reported"
    MIXED = "mixed"
    UNSPECIFIED = "unspecified"


class RuntimeCompletenessClass(str, Enum):
    MORE_COMPLETE = "more_complete"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class RuntimeGraphContractView:
    source_mode: RuntimeSourceMode
    negation_present: bool
    modality_or_interrogative_present: bool
    dictum_modus_linked: bool
    completeness_class: RuntimeCompletenessClass
    ambiguity_preserved: bool
    unresolved_structure_present: bool
    usability_class: GraphUsabilityClass
    restrictions: tuple[str, ...]
    requires_restriction_read: bool
    strong_semantic_settlement_permitted: bool
    can_distinguish_source_mode: bool
    can_distinguish_operator_mode: bool
    reason: str


def derive_runtime_graph_contract_view(
    runtime_graph_result_or_bundle: RuntimeGraphResult | RuntimeGraphBundle,
) -> RuntimeGraphContractView:
    if isinstance(runtime_graph_result_or_bundle, RuntimeGraphResult):
        bundle = runtime_graph_result_or_bundle.bundle
    elif isinstance(runtime_graph_result_or_bundle, RuntimeGraphBundle):
        bundle = runtime_graph_result_or_bundle
    else:
        raise TypeError(
            "derive_runtime_graph_contract_view requires RuntimeGraphResult/RuntimeGraphBundle"
        )

    gate = evaluate_runtime_graph_downstream_gate(bundle)
    certainties = {candidate.certainty_class for candidate in bundle.proposition_candidates}
    if CertaintyClass.QUOTED in certainties and CertaintyClass.REPORTED in certainties:
        source_mode = RuntimeSourceMode.MIXED
    elif CertaintyClass.QUOTED in certainties:
        source_mode = RuntimeSourceMode.QUOTED
    elif CertaintyClass.REPORTED in certainties:
        source_mode = RuntimeSourceMode.REPORTED
    elif certainties:
        source_mode = RuntimeSourceMode.ASSERTED
    else:
        source_mode = RuntimeSourceMode.UNSPECIFIED

    negation_present = any(candidate.polarity is PolarityClass.NEGATED for candidate in bundle.proposition_candidates)
    modality_or_interrogative_present = any(
        candidate.certainty_class in {CertaintyClass.HYPOTHETICAL, CertaintyClass.INTERROGATIVE}
        for candidate in bundle.proposition_candidates
    )
    dictum_modus_linked = any(edge.edge_kind == "modus_to_dictum" for edge in bundle.graph_edges)
    unresolved_structure_present = bool(bundle.unresolved_role_slots) or any(
        candidate.unresolved for candidate in bundle.proposition_candidates
    )
    ambiguity_preserved = bool(bundle.graph_alternatives or bundle.ambiguity_reasons)
    completeness_class = (
        RuntimeCompletenessClass.INCOMPLETE if unresolved_structure_present else RuntimeCompletenessClass.MORE_COMPLETE
    )
    requires_restriction_read = True
    strong_semantic_settlement_permitted = False
    can_distinguish_source_mode = source_mode is not RuntimeSourceMode.UNSPECIFIED
    can_distinguish_operator_mode = negation_present or modality_or_interrogative_present or dictum_modus_linked
    reason = (
        "g02 contract view exposes bounded runtime distinctions; restrictions are mandatory"
        if gate.accepted
        else "g02 contract view blocked by runtime graph gate"
    )
    return RuntimeGraphContractView(
        source_mode=source_mode,
        negation_present=negation_present,
        modality_or_interrogative_present=modality_or_interrogative_present,
        dictum_modus_linked=dictum_modus_linked,
        completeness_class=completeness_class,
        ambiguity_preserved=ambiguity_preserved,
        unresolved_structure_present=unresolved_structure_present,
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        requires_restriction_read=requires_restriction_read,
        strong_semantic_settlement_permitted=strong_semantic_settlement_permitted,
        can_distinguish_source_mode=can_distinguish_source_mode,
        can_distinguish_operator_mode=can_distinguish_operator_mode,
        reason=reason,
    )

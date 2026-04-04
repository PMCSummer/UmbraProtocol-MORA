from __future__ import annotations

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.grounded_semantic.models import (
    GroundedSemanticBundle,
    GroundedSemanticResult,
    GroundedUnitKind,
    OperatorKind,
    SourceAnchorKind,
    UncertaintyKind,
)
from substrate.runtime_semantic_graph.models import (
    CertaintyClass,
    DictumOrModusClass,
    GraphAlternative,
    GraphEdge,
    PolarityClass,
    PropositionCandidate,
    RoleBinding,
    RuntimeGraphBundle,
    RuntimeGraphResult,
    SemanticUnit,
    SemanticUnitKind,
)
from substrate.runtime_semantic_graph.policy import evaluate_runtime_graph_downstream_gate
from substrate.runtime_semantic_graph.telemetry import (
    build_runtime_graph_telemetry,
    runtime_graph_result_snapshot,
)
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "g02.validate_typed_inputs",
    "g02.frame_instantiation",
    "g02.role_binding",
    "g02.operator_source_propagation",
    "g02.proposition_candidate_formation",
    "g02.ambiguity_preservation",
    "g02.downstream_gate",
)


def build_runtime_semantic_graph(
    grounded_result_or_bundle: GroundedSemanticResult | GroundedSemanticBundle,
) -> RuntimeGraphResult:
    grounded_bundle, source_lineage = _extract_grounded_input(grounded_result_or_bundle)
    if not grounded_bundle.phrase_scaffolds or not grounded_bundle.dictum_carriers:
        return _abstain_result(
            grounded_bundle=grounded_bundle,
            source_lineage=source_lineage,
            reason="grounded substrate missing scaffold/dictum carriers",
        )

    unit_index = 0
    binding_index = 0
    edge_index = 0
    proposition_index = 0
    alternative_index = 0

    semantic_units: list[SemanticUnit] = []
    role_bindings: list[RoleBinding] = []
    edges: list[GraphEdge] = []
    propositions: list[PropositionCandidate] = []
    alternatives: list[GraphAlternative] = []
    unresolved_role_slots: list[str] = []
    low_coverage_reasons: list[str] = list(grounded_bundle.low_coverage_reasons)
    ambiguity_reasons: list[str] = list(grounded_bundle.ambiguity_reasons)

    predicate_units = [u for u in grounded_bundle.substrate_units if u.unit_kind is GroundedUnitKind.PREDICATE]
    source_anchor_ids = tuple(anchor.anchor_id for anchor in grounded_bundle.source_anchors)
    source_kinds = {anchor.anchor_kind for anchor in grounded_bundle.source_anchors}

    for idx, dictum in enumerate(grounded_bundle.dictum_carriers):
        scaffold = grounded_bundle.phrase_scaffolds[idx] if idx < len(grounded_bundle.phrase_scaffolds) else None
        predicate_text = _choose_predicate_text(predicate_units, scaffold)
        polarity = _derive_polarity(grounded_bundle, dictum.dictum_candidate_id)
        certainty = _derive_certainty(grounded_bundle, source_kinds, dictum.dictum_candidate_id)

        unit_index += 1
        frame_id = f"frame-{unit_index}"
        semantic_units.append(
            SemanticUnit(
                semantic_unit_id=frame_id,
                unit_kind=SemanticUnitKind.FRAME_NODE,
                predicate=predicate_text,
                role_bindings=(),
                modifier_links=(),
                source_scope=source_anchor_ids,
                dictum_or_modus_class=DictumOrModusClass.DICTUM,
                polarity=polarity,
                certainty_class=certainty,
                provenance="g02 frame node from g01 dictum/scaffold",
                confidence=max(0.2, min(0.95, dictum.confidence)),
            )
        )

        frame_binding_ids: list[str] = []
        if scaffold and scaffold.candidate_head_links:
            unresolved_markers = tuple(scaffold.unresolved_attachments)
            for _, target_ref in scaffold.candidate_head_links:
                binding_index += 1
                binding_id = f"binding-{binding_index}"
                unresolved = any(target_ref in marker for marker in unresolved_markers)
                reason = "upstream unresolved attachment" if unresolved else None
                if unresolved:
                    unresolved_role_slots.append(binding_id)
                role_bindings.append(
                    RoleBinding(
                        binding_id=binding_id,
                        frame_node_id=frame_id,
                        role_label=f"arg:{target_ref}",
                        target_ref=target_ref,
                        unresolved=unresolved,
                        unresolved_reason=reason,
                        confidence=0.5 if unresolved else 0.72,
                        provenance="g02 role binding from g01 candidate head links",
                    )
                )
                frame_binding_ids.append(binding_id)
                edge_index += 1
                edges.append(
                    GraphEdge(
                        edge_id=f"edge-{edge_index}",
                        source_node_id=frame_id,
                        target_node_id=target_ref,
                        edge_kind="role_binding",
                        uncertain=unresolved,
                        reason=reason,
                        confidence=0.52 if unresolved else 0.78,
                    )
                )
        else:
            binding_index += 1
            unresolved_id = f"binding-{binding_index}"
            unresolved_role_slots.append(unresolved_id)
            role_bindings.append(
                RoleBinding(
                    binding_id=unresolved_id,
                    frame_node_id=frame_id,
                    role_label="arg:unresolved",
                    target_ref=None,
                    unresolved=True,
                    unresolved_reason="missing explicit role links in g01 scaffold",
                    confidence=0.3,
                    provenance="g02 unresolved role placeholder",
                )
            )
            frame_binding_ids.append(unresolved_id)

        has_unresolved_binding = any(
            binding.unresolved for binding in role_bindings if binding.binding_id in frame_binding_ids
        )
        has_binding_uncertainty_hint = any(
            marker.uncertainty_kind in {UncertaintyKind.ATTACHMENT_AMBIGUOUS, UncertaintyKind.REFERENT_UNRESOLVED}
            for marker in grounded_bundle.uncertainty_markers
        )
        if not has_unresolved_binding and len(frame_binding_ids) <= 1 and (
            has_binding_uncertainty_hint or grounded_bundle.low_coverage_mode
        ):
            binding_index += 1
            inferred_unresolved_id = f"binding-{binding_index}"
            unresolved_role_slots.append(inferred_unresolved_id)
            role_bindings.append(
                RoleBinding(
                    binding_id=inferred_unresolved_id,
                    frame_node_id=frame_id,
                    role_label="arg:unresolved_placeholder",
                    target_ref=None,
                    unresolved=True,
                    unresolved_reason="sparse role evidence with unresolved upstream cues",
                    confidence=0.28,
                    provenance="g02 unresolved role placeholder from sparse binding evidence",
                )
            )
            frame_binding_ids.append(inferred_unresolved_id)

        proposition_index += 1
        proposition_id = f"prop-{proposition_index}"
        unresolved_prop = any(binding.unresolved for binding in role_bindings if binding.binding_id in frame_binding_ids)
        propositions.append(
            PropositionCandidate(
                proposition_id=proposition_id,
                frame_node_id=frame_id,
                role_binding_ids=tuple(frame_binding_ids),
                source_scope_refs=source_anchor_ids,
                dictum_or_modus_class=DictumOrModusClass.DICTUM,
                polarity=polarity,
                certainty_class=certainty,
                unresolved=unresolved_prop,
                confidence=max(0.2, min(0.9, 0.72 - (0.18 if unresolved_prop else 0.0))),
                provenance="g02 proposition candidate from frame+bindings",
            )
        )

    for modus in grounded_bundle.modus_carriers:
        unit_index += 1
        modus_id = f"modus-{unit_index}"
        certainty = _certainty_from_modus_kind(modus.stance_kind)
        semantic_units.append(
            SemanticUnit(
                semantic_unit_id=modus_id,
                unit_kind=SemanticUnitKind.MODUS_NODE,
                predicate=None,
                role_bindings=(),
                modifier_links=modus.evidence_refs,
                source_scope=source_anchor_ids,
                dictum_or_modus_class=DictumOrModusClass.MODUS,
                polarity=PolarityClass.UNKNOWN,
                certainty_class=certainty,
                provenance="g02 modus node from g01 modus carrier",
                confidence=max(0.2, min(0.88, modus.confidence)),
            )
        )
        for frame in [u for u in semantic_units if u.unit_kind is SemanticUnitKind.FRAME_NODE]:
            edge_index += 1
            edges.append(
                GraphEdge(
                    edge_id=f"edge-{edge_index}",
                    source_node_id=modus_id,
                    target_node_id=frame.semantic_unit_id,
                    edge_kind="modus_to_dictum",
                    uncertain=modus.unresolved,
                    reason="modus link unresolved" if modus.unresolved else None,
                    confidence=0.5 if modus.unresolved else 0.74,
                )
            )

    for operator in grounded_bundle.operator_carriers:
        unit_index += 1
        op_id = f"op-node-{unit_index}"
        semantic_units.append(
            SemanticUnit(
                semantic_unit_id=op_id,
                unit_kind=SemanticUnitKind.OPERATOR_NODE,
                predicate=operator.operator_kind.value,
                role_bindings=(),
                modifier_links=operator.scope_anchor_refs,
                source_scope=source_anchor_ids,
                dictum_or_modus_class=DictumOrModusClass.MODUS,
                polarity=PolarityClass.UNKNOWN,
                certainty_class=CertaintyClass.UNCERTAIN if operator.scope_uncertain else CertaintyClass.ASSERTED,
                provenance="g02 operator node from g01 operator carrier",
                confidence=max(0.2, min(0.86, operator.confidence)),
            )
        )
        for frame in [u for u in semantic_units if u.unit_kind is SemanticUnitKind.FRAME_NODE]:
            edge_index += 1
            edges.append(
                GraphEdge(
                    edge_id=f"edge-{edge_index}",
                    source_node_id=op_id,
                    target_node_id=frame.semantic_unit_id,
                    edge_kind=f"operator_scope:{operator.operator_kind.value}",
                    uncertain=operator.scope_uncertain,
                    reason="operator scope uncertain" if operator.scope_uncertain else None,
                    confidence=0.48 if operator.scope_uncertain else 0.77,
                )
            )

    for marker in grounded_bundle.uncertainty_markers:
        alternative_index += 1
        alternatives.append(
            GraphAlternative(
                alternative_id=f"alt-{alternative_index}",
                competing_ref_ids=marker.related_refs,
                reason=marker.reason,
                confidence=marker.confidence,
            )
        )

    if grounded_bundle.ambiguity_reasons:
        for reason in grounded_bundle.ambiguity_reasons:
            alternative_index += 1
            alternatives.append(
                GraphAlternative(
                    alternative_id=f"alt-{alternative_index}",
                    competing_ref_ids=grounded_bundle.linked_dictum_candidate_ids,
                    reason=reason,
                    confidence=0.42,
                )
            )

    if not grounded_bundle.operator_carriers:
        low_coverage_reasons.append("operator_carriers_missing")
    if not grounded_bundle.source_anchors:
        low_coverage_reasons.append("source_anchors_missing")
    if not grounded_bundle.modus_carriers:
        low_coverage_reasons.append("modus_carriers_missing")
    if not semantic_units:
        low_coverage_reasons.append("semantic_units_missing")
    if not propositions:
        low_coverage_reasons.append("proposition_candidates_missing")

    low_coverage_mode = bool(low_coverage_reasons)
    bundle = RuntimeGraphBundle(
        source_grounded_ref=grounded_bundle.source_dictum_ref,
        source_dictum_ref=grounded_bundle.source_dictum_ref,
        source_syntax_ref=grounded_bundle.source_syntax_ref,
        source_surface_ref=grounded_bundle.source_surface_ref,
        linked_scaffold_ids=tuple(scaffold.scaffold_id for scaffold in grounded_bundle.phrase_scaffolds),
        linked_dictum_ids=grounded_bundle.linked_dictum_candidate_ids,
        semantic_units=tuple(semantic_units),
        role_bindings=tuple(role_bindings),
        graph_edges=tuple(edges),
        proposition_candidates=tuple(propositions),
        graph_alternatives=tuple(alternatives),
        unresolved_role_slots=tuple(dict.fromkeys(unresolved_role_slots)),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        low_coverage_mode=low_coverage_mode,
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage_reasons)),
        no_final_semantic_closure=True,
        reason="g02 compiled bounded runtime graph from g01 scaffold without semantic closure",
    )
    gate = evaluate_runtime_graph_downstream_gate(bundle)
    source_lineage = tuple(
        dict.fromkeys(
            (
                grounded_bundle.source_dictum_ref,
                grounded_bundle.source_syntax_ref,
                *((grounded_bundle.source_surface_ref,) if grounded_bundle.source_surface_ref else ()),
                *source_lineage,
            )
        )
    )
    telemetry = build_runtime_graph_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="g01 scaffold compiled into frame-role-proposition runtime graph with preserved uncertainty",
    )
    confidence = _estimate_result_confidence(bundle)
    partial_known = bool(bundle.low_coverage_mode or bundle.unresolved_role_slots or bundle.graph_alternatives)
    partial_known_reason = (
        "; ".join(bundle.low_coverage_reasons)
        if bundle.low_coverage_reasons
        else ("graph alternatives preserved" if bundle.graph_alternatives else None)
    )
    abstain = not gate.accepted
    abstain_reason = None if gate.accepted else gate.reason
    return RuntimeGraphResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_final_semantic_closure=True,
    )


def runtime_graph_result_to_payload(result: RuntimeGraphResult) -> dict[str, object]:
    return runtime_graph_result_snapshot(result)


def persist_runtime_graph_result_via_f01(
    *,
    result: RuntimeGraphResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("g02-runtime-semantic-graph",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"runtime-graph-step-{transition_id}",
            "runtime_semantic_graph_snapshot": runtime_graph_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_grounded_input(
    grounded_result_or_bundle: GroundedSemanticResult | GroundedSemanticBundle,
) -> tuple[GroundedSemanticBundle, tuple[str, ...]]:
    if isinstance(grounded_result_or_bundle, GroundedSemanticResult):
        return grounded_result_or_bundle.bundle, grounded_result_or_bundle.telemetry.source_lineage
    if isinstance(grounded_result_or_bundle, GroundedSemanticBundle):
        return grounded_result_or_bundle, ()
    raise TypeError(
        "build_runtime_semantic_graph requires GroundedSemanticResult or GroundedSemanticBundle"
    )


def _choose_predicate_text(predicate_units, scaffold) -> str:
    if scaffold is not None:
        for unit in predicate_units:
            if any(boundary.start <= unit.span_start <= boundary.end for boundary in scaffold.clause_boundaries):
                return unit.normalized_form
    if predicate_units:
        return predicate_units[0].normalized_form
    return "predicate_unresolved"


def _derive_polarity(bundle: GroundedSemanticBundle, dictum_id: str) -> PolarityClass:
    negated = any(
        carrier.operator_kind is OperatorKind.NEGATION
        and (not carrier.scope_anchor_refs or dictum_id in carrier.scope_anchor_refs)
        for carrier in bundle.operator_carriers
    )
    return PolarityClass.NEGATED if negated else PolarityClass.AFFIRMATIVE


def _derive_certainty(
    bundle: GroundedSemanticBundle,
    source_kinds: set[SourceAnchorKind],
    dictum_id: str,
) -> CertaintyClass:
    has_interrogation = any(
        carrier.operator_kind is OperatorKind.INTERROGATION
        and (not carrier.scope_anchor_refs or dictum_id in carrier.scope_anchor_refs)
        for carrier in bundle.operator_carriers
    )
    has_modality = any(
        carrier.operator_kind in {OperatorKind.MODALITY, OperatorKind.DISCOURSE_PARTICLE}
        and (not carrier.scope_anchor_refs or dictum_id in carrier.scope_anchor_refs)
        for carrier in bundle.operator_carriers
    )
    if SourceAnchorKind.REPORTED_SPEECH in source_kinds:
        return CertaintyClass.REPORTED
    if SourceAnchorKind.QUOTE_BOUNDARY in source_kinds:
        return CertaintyClass.QUOTED
    if has_interrogation:
        return CertaintyClass.INTERROGATIVE
    if has_modality:
        return CertaintyClass.HYPOTHETICAL
    has_uncertainty = any(
        marker.uncertainty_kind
        in {
            UncertaintyKind.OPERATOR_SCOPE_UNCERTAIN,
            UncertaintyKind.SOURCE_SCOPE_UNCERTAIN,
            UncertaintyKind.ATTACHMENT_AMBIGUOUS,
        }
        for marker in bundle.uncertainty_markers
    )
    return CertaintyClass.UNCERTAIN if has_uncertainty else CertaintyClass.ASSERTED


def _certainty_from_modus_kind(kind: str) -> CertaintyClass:
    lowered = kind.lower()
    if "interrog" in lowered:
        return CertaintyClass.INTERROGATIVE
    if "modal" in lowered:
        return CertaintyClass.HYPOTHETICAL
    if "report" in lowered:
        return CertaintyClass.REPORTED
    if "quotation" in lowered:
        return CertaintyClass.QUOTED
    return CertaintyClass.UNCERTAIN


def _estimate_result_confidence(bundle: RuntimeGraphBundle) -> float:
    base = 0.76
    base -= min(0.26, len(bundle.unresolved_role_slots) * 0.04)
    base -= min(0.24, len(bundle.graph_alternatives) * 0.015)
    if bundle.low_coverage_mode:
        base -= min(0.28, len(bundle.low_coverage_reasons) * 0.05)
    if not bundle.proposition_candidates:
        base -= 0.24
    return max(0.08, min(0.92, round(base, 4)))


def _abstain_result(
    *,
    grounded_bundle: GroundedSemanticBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> RuntimeGraphResult:
    bundle = RuntimeGraphBundle(
        source_grounded_ref=grounded_bundle.source_dictum_ref,
        source_dictum_ref=grounded_bundle.source_dictum_ref,
        source_syntax_ref=grounded_bundle.source_syntax_ref,
        source_surface_ref=grounded_bundle.source_surface_ref,
        linked_scaffold_ids=tuple(scaffold.scaffold_id for scaffold in grounded_bundle.phrase_scaffolds),
        linked_dictum_ids=grounded_bundle.linked_dictum_candidate_ids,
        semantic_units=(),
        role_bindings=(),
        graph_edges=(),
        proposition_candidates=(),
        graph_alternatives=(
            GraphAlternative(
                alternative_id="alt-abstain",
                competing_ref_ids=grounded_bundle.linked_dictum_candidate_ids,
                reason=reason,
                confidence=0.2,
            ),
        ),
        unresolved_role_slots=("binding:abstain",),
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=("abstain",),
        no_final_semantic_closure=True,
        reason="g02 abstained due to insufficient g01 scaffold basis",
    )
    gate = evaluate_runtime_graph_downstream_gate(bundle)
    telemetry = build_runtime_graph_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="insufficient g01 scaffold -> g02 abstain",
    )
    return RuntimeGraphResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.08,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_semantic_closure=True,
    )

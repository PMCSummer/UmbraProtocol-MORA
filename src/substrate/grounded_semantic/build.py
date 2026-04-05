from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.dictum_candidates.models import DictumCandidateBundle, DictumCandidateResult
from substrate.discourse_update.models import (
    AcceptanceStatus,
    ContinuationStatus,
    DiscourseUpdateBundle,
    DiscourseUpdateResult,
    ProposalType,
    RepairClass,
)
from substrate.grounded_semantic.models import (
    AmbiguityState,
    CarrierKind,
    ChannelOrigin,
    DictumCarrier,
    G01EvidenceKind,
    G01EvidenceRecord,
    GroundedSemanticBundle,
    GroundedSemanticResult,
    G01CoverageCode,
    G01NormativeBindingFailureCode,
    GroundedSubstrateUnit,
    ModusCarrier,
    OperatorAttachment,
    OperatorCarrier,
    OperatorKind,
    PhraseScaffold,
    SourceAnchor,
    SourceAnchorKind,
    SpanRange,
    UncertaintyKind,
    UncertaintyMarker,
    GroundedUnitKind,
)
from substrate.grounded_semantic.policy import evaluate_grounded_semantic_downstream_gate
from substrate.grounded_semantic.telemetry import (
    build_grounded_semantic_telemetry,
    grounded_semantic_result_snapshot,
)
from substrate.language_surface.models import UtteranceSurface, UtteranceSurfaceResult
from substrate.modus_hypotheses.models import (
    AddressivityKind,
    IllocutionKind,
    L05CautionCode,
    ModusEvidenceKind,
    ModusHypothesisBundle,
    ModusHypothesisRecord,
    ModusHypothesisResult,
)
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "g01.validate_typed_inputs",
    "g01.normative_l05_l06_intake",
    "g01.substrate_unit_projection",
    "g01.phrase_scaffold_building",
    "g01.operator_carrier_projection",
    "g01.dictum_modus_split",
    "g01.source_anchor_projection",
    "g01.uncertainty_marking",
    "g01.downstream_gate",
)

_REPORT_CUE_PATTERN = re.compile(
    r"\b(says|said|report(?:ed|s)?|according|говорит|сказал|сказала|сообщил|по\s+словам)\b",
    re.IGNORECASE,
)
_MODAL_CUE_PATTERN = re.compile(
    r"\b(may|might|must|should|can|could|maybe|perhaps|может|должен|должна|вероятно|возможно)\b",
    re.IGNORECASE,
)
_COORDINATION_CUE_PATTERN = re.compile(r"\b(and|or|и|или|либо)\b", re.IGNORECASE)
_CONDITIONAL_CUE_PATTERN = re.compile(r"\b(if|unless|если|когда\s+бы)\b", re.IGNORECASE)
_STANCE_PARTICLE_PATTERN = re.compile(r"\b(well|just|even|же|ведь|ли|уж)\b", re.IGNORECASE)
_SPEAKER_PATTERN = re.compile(r"\b(i|we|я|мы)\b", re.IGNORECASE)
_DEIXIS_PATTERN = re.compile(r"\b(this|that|here|there|now|then|это|там|здесь|сейчас|тогда)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class _G01SourceRefs:
    source_modus_ref: str | None
    source_modus_ref_kind: str
    source_modus_lineage_ref: str | None
    source_discourse_update_ref: str | None
    source_discourse_update_ref_kind: str
    source_discourse_update_lineage_ref: str | None


def build_grounded_semantic_substrate(
    dictum_result_or_bundle: DictumCandidateResult | DictumCandidateBundle,
    utterance_surface: UtteranceSurface | UtteranceSurfaceResult | None = None,
    memory_anchor_ref: str | None = None,
    cooperation_anchor_ref: str | None = None,
    modus_hypotheses_result_or_bundle: ModusHypothesisResult | ModusHypothesisBundle | None = None,
    discourse_update_result_or_bundle: DiscourseUpdateResult | DiscourseUpdateBundle | None = None,
) -> GroundedSemanticResult:
    dictum_bundle, dictum_lineage = _extract_dictum_input(dictum_result_or_bundle)
    modus_bundle, modus_lineage = _extract_optional_modus_input(modus_hypotheses_result_or_bundle)
    discourse_bundle, discourse_lineage = _extract_optional_discourse_update_input(discourse_update_result_or_bundle)
    surface = _extract_optional_surface(utterance_surface)
    if memory_anchor_ref is not None and not isinstance(memory_anchor_ref, str):
        raise TypeError("memory_anchor_ref must be str when provided")
    if cooperation_anchor_ref is not None and not isinstance(cooperation_anchor_ref, str):
        raise TypeError("cooperation_anchor_ref must be str when provided")
    if (modus_bundle is None) ^ (discourse_bundle is None):
        raise TypeError(
            "normative g01 intake requires both typed L05 and typed L06 artifacts together, or neither"
        )
    if modus_bundle is None and discourse_bundle is None:
        raise TypeError(
            "g01 construction requires typed L05+L06 inputs on canonical production route; "
            "legacy L04-only compatibility route has been retired"
        )
    if (
        modus_bundle is not None
        and discourse_bundle is not None
        and (binding_failure := _normative_binding_failure_code(
            dictum_bundle=dictum_bundle,
            modus_bundle=modus_bundle,
            discourse_bundle=discourse_bundle,
        ))
        is not None
    ):
        raise TypeError(
            "typed L05/L06 bindings are incompatible with current L04 dictum basis; "
            "g01 will not silently downgrade to legacy surface fallback on normative entrypoint "
            f"[{binding_failure.value}]"
        )

    if not dictum_bundle.dictum_candidates:
        return _abstain_result(
            dictum_bundle=dictum_bundle,
            source_lineage=dictum_lineage,
            reason="dictum candidate bundle is empty",
        )

    raw_text = surface.raw_text if surface is not None else ""
    unit_index = 0
    carrier_index = 0
    anchor_index = 0
    uncertainty_index = 0
    scaffold_index = 0
    evidence_index = 0

    substrate_units: list[GroundedSubstrateUnit] = []
    phrase_scaffolds: list[PhraseScaffold] = []
    operator_carriers: list[OperatorCarrier] = []
    dictum_carriers: list[DictumCarrier] = []
    modus_carriers: list[ModusCarrier] = []
    source_anchors: list[SourceAnchor] = []
    uncertainty_markers: list[UncertaintyMarker] = []
    evidence_records: list[G01EvidenceRecord] = []
    ambiguity_reasons: list[str] = []
    low_coverage_reasons: list[str] = []
    clause_ranges_by_id: dict[str, list[tuple[int, int]]] = defaultdict(list)
    dictum_span_by_id = {
        candidate.dictum_candidate_id: (
            candidate.predicate_frame.predicate_span.start,
            candidate.predicate_frame.predicate_span.end,
        )
        for candidate in dictum_bundle.dictum_candidates
    }
    normative_route_binding_valid = False
    normative_l05_l06_route_active = False
    legacy_surface_cue_fallback_used = False
    discourse_update_not_inferred_from_surface_when_l06_available = False
    l06_blocked_update_present = False
    l06_guarded_continue_present = False
    source_refs = _derive_source_refs(modus_bundle=modus_bundle, discourse_bundle=discourse_bundle)

    for candidate in dictum_bundle.dictum_candidates:
        clause_start = candidate.predicate_frame.predicate_span.start
        clause_end = candidate.predicate_frame.predicate_span.end
        phrase_ranges: list[SpanRange] = [
            SpanRange(
                start=candidate.predicate_frame.predicate_span.start,
                end=candidate.predicate_frame.predicate_span.end,
            )
        ]

        unit_index += 1
        predicate_unit_id = f"unit-{unit_index}"
        predicate_raw = _slice_text(raw_text, candidate.predicate_frame.predicate_span.start, candidate.predicate_frame.predicate_span.end)
        substrate_units.append(
            GroundedSubstrateUnit(
                unit_id=predicate_unit_id,
                span_start=candidate.predicate_frame.predicate_span.start,
                span_end=candidate.predicate_frame.predicate_span.end,
                raw_surface=predicate_raw,
                normalized_form=predicate_raw.lower() if predicate_raw else candidate.predicate_frame.predicate_token_id.lower(),
                unit_kind=GroundedUnitKind.PREDICATE,
                channel_origin=ChannelOrigin.L04_DICTUM,
                confidence=candidate.predicate_frame.confidence,
                provenance="g01 projected predicate unit from l04 predicate_frame",
                ambiguity_state=AmbiguityState.AMBIGUOUS if candidate.ambiguity_reasons else AmbiguityState.PROVISIONAL,
            )
        )

        head_links: list[tuple[str, str]] = []
        unresolved_attachments: list[str] = []
        argument_slot_refs: list[str] = []

        for slot in candidate.argument_slots:
            clause_start = min(clause_start, slot.token_span.start)
            clause_end = max(clause_end, slot.token_span.end)
            phrase_ranges.append(SpanRange(start=slot.token_span.start, end=slot.token_span.end))
            head_links.append((candidate.predicate_frame.predicate_token_id, slot.token_id))
            argument_slot_refs.append(slot.slot_id)
            if slot.unresolved and slot.unresolved_reason:
                unresolved_attachments.append(f"{slot.slot_id}:{slot.unresolved_reason}")

            unit_index += 1
            slot_raw = _slice_text(raw_text, slot.token_span.start, slot.token_span.end)
            substrate_units.append(
                GroundedSubstrateUnit(
                    unit_id=f"unit-{unit_index}",
                    span_start=slot.token_span.start,
                    span_end=slot.token_span.end,
                    raw_surface=slot_raw,
                    normalized_form=slot_raw.lower() if slot_raw else slot.token_id.lower(),
                    unit_kind=GroundedUnitKind.ARGUMENT,
                    channel_origin=ChannelOrigin.L04_DICTUM,
                    confidence=slot.confidence,
                    provenance="g01 projected argument unit from l04 argument_slot",
                    ambiguity_state=AmbiguityState.UNRESOLVED if slot.unresolved else AmbiguityState.PROVISIONAL,
                )
            )
            if slot.unresolved:
                uncertainty_index += 1
                uncertainty_markers.append(
                    UncertaintyMarker(
                        marker_id=f"uncertainty-{uncertainty_index}",
                        uncertainty_kind=(
                            UncertaintyKind.REFERENT_UNRESOLVED
                            if "reference" in (slot.unresolved_reason or "") or "deixis" in (slot.unresolved_reason or "")
                            else UncertaintyKind.ATTACHMENT_AMBIGUOUS
                        ),
                        related_refs=(slot.slot_id, slot.token_id),
                        reason=slot.unresolved_reason or "argument slot unresolved",
                        confidence=0.34,
                    )
                )

        clause_ranges_by_id[candidate.predicate_frame.clause_id].append((clause_start, clause_end))
        local_scope_relations: list[str] = []
        operator_attachments: list[OperatorAttachment] = []

        for marker in candidate.scope_markers:
            carrier_index += 1
            op_id = f"op-{carrier_index}"
            operator_carriers.append(
                OperatorCarrier(
                    operator_id=op_id,
                    operator_kind=_operator_kind_from_scope_marker(marker.marker_kind),
                    carrier_unit_ids=tuple(marker.affected_slot_ids),
                    scope_anchor_refs=(candidate.dictum_candidate_id,),
                    scope_uncertain=marker.ambiguous,
                    confidence=marker.confidence,
                    provenance="g01 scope operator carrier from l04 scope marker",
                )
            )
            operator_attachments.append(
                OperatorAttachment(
                    operator_id=op_id,
                    target_ref=candidate.dictum_candidate_id,
                    relation=marker.marker_kind,
                    unresolved=marker.ambiguous,
                    reason=marker.reason,
                )
            )
            local_scope_relations.append(marker.marker_kind)
            if marker.ambiguous:
                uncertainty_index += 1
                uncertainty_markers.append(
                    UncertaintyMarker(
                        marker_id=f"uncertainty-{uncertainty_index}",
                        uncertainty_kind=UncertaintyKind.OPERATOR_SCOPE_UNCERTAIN,
                        related_refs=(marker.scope_marker_id, candidate.dictum_candidate_id),
                        reason=marker.reason,
                        confidence=marker.confidence,
                    )
                )

        for marker in candidate.negation_markers:
            carrier_index += 1
            op_id = f"op-{carrier_index}"
            operator_carriers.append(
                OperatorCarrier(
                    operator_id=op_id,
                    operator_kind=OperatorKind.NEGATION,
                    carrier_unit_ids=tuple(marker.carrier_token_ids),
                    scope_anchor_refs=(candidate.dictum_candidate_id,),
                    scope_uncertain=marker.scope_ambiguous,
                    confidence=marker.confidence,
                    provenance="g01 negation operator carrier from l04 negation marker",
                )
            )
            operator_attachments.append(
                OperatorAttachment(
                    operator_id=op_id,
                    target_ref=candidate.dictum_candidate_id,
                    relation="negation_scope",
                    unresolved=marker.scope_ambiguous,
                    reason=marker.reason,
                )
            )
            if marker.scope_ambiguous:
                uncertainty_index += 1
                uncertainty_markers.append(
                    UncertaintyMarker(
                        marker_id=f"uncertainty-{uncertainty_index}",
                        uncertainty_kind=UncertaintyKind.OPERATOR_SCOPE_UNCERTAIN,
                        related_refs=(marker.negation_marker_id, candidate.dictum_candidate_id),
                        reason=marker.reason,
                        confidence=marker.confidence,
                    )
                )

        scaffold_index += 1
        phrase_scaffolds.append(
            PhraseScaffold(
                scaffold_id=f"scaffold-{scaffold_index}",
                clause_boundaries=(SpanRange(start=clause_start, end=clause_end),),
                phrase_boundaries=tuple(phrase_ranges),
                operator_attachments=tuple(operator_attachments),
                local_scope_relations=tuple(dict.fromkeys(local_scope_relations)),
                candidate_head_links=tuple(head_links),
                unresolved_attachments=tuple(unresolved_attachments),
                confidence=max(0.2, min(0.92, candidate.confidence)),
                provenance="g01 phrase scaffold from l04 dictum candidate",
            )
        )

        carrier_index += 1
        dictum_carriers.append(
            DictumCarrier(
                carrier_id=f"carrier-{carrier_index}",
                dictum_candidate_id=candidate.dictum_candidate_id,
                predicate_ref=candidate.predicate_frame.frame_id,
                argument_slot_refs=tuple(argument_slot_refs),
                confidence=max(0.2, min(0.95, candidate.confidence)),
                provenance="g01 dictum content carrier from l04 candidate",
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.DICTUM_CARRIER,
            source_ref_ids=(candidate.dictum_candidate_id, candidate.predicate_frame.frame_id),
            supports_dimensions=("dictum_content",),
            unresolved=bool(candidate.underspecified_slots or candidate.ambiguity_reasons),
            route_class="shared",
            reason="dictum carrier assembled from l04 candidate basis",
        )

        if candidate.quotation_sensitive:
            carrier_index += 1
            modus_carriers.append(
                ModusCarrier(
                    carrier_id=f"carrier-{carrier_index}",
                    dictum_candidate_id=candidate.dictum_candidate_id,
                    stance_kind=CarrierKind.MODUS_STANCE.value + ":quotation_sensitive",
                    evidence_refs=(candidate.predicate_frame.frame_id,),
                    unresolved=True,
                    confidence=0.42,
                    provenance="g01 modus carrier from quotation-sensitive dictum marker",
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.MODUS_CARRIER,
                source_ref_ids=(candidate.dictum_candidate_id, "quotation_sensitive"),
                supports_dimensions=("modus_stance", "quotation"),
                unresolved=True,
                route_class="shared",
                reason="quotation-sensitive dictum contributes unresolved modus carrier",
            )

    if modus_bundle is not None and discourse_bundle is not None:
        normative_route_binding_valid = True
        (
            anchor_index,
            carrier_index,
            uncertainty_index,
            evidence_index,
            l06_blocked_update_present,
            l06_guarded_continue_present,
        ) = _register_normative_l05_l06_cues(
            dictum_bundle=dictum_bundle,
            dictum_span_by_id=dictum_span_by_id,
            modus_bundle=modus_bundle,
            discourse_bundle=discourse_bundle,
            source_anchors=source_anchors,
            operator_carriers=operator_carriers,
            modus_carriers=modus_carriers,
            uncertainty_markers=uncertainty_markers,
            evidence_records=evidence_records,
            start_anchor_index=anchor_index,
            start_carrier_index=carrier_index,
            start_uncertainty_index=uncertainty_index,
            start_evidence_index=evidence_index,
        )
        normative_l05_l06_route_active = True
        discourse_update_not_inferred_from_surface_when_l06_available = True
        low_coverage_reasons.append(G01CoverageCode.L05_L06_NORMATIVE_ROUTE_ACTIVE)
        if l06_blocked_update_present:
            low_coverage_reasons.append(G01CoverageCode.L06_BLOCKED_UPDATE_PRESENT)
        if l06_guarded_continue_present:
            low_coverage_reasons.append(G01CoverageCode.L06_GUARDED_CONTINUE_PRESENT)

    for clause_id, ranges in clause_ranges_by_id.items():
        if len(set(ranges)) > 1:
            uncertainty_index += 1
            uncertainty_markers.append(
                UncertaintyMarker(
                    marker_id=f"uncertainty-{uncertainty_index}",
                    uncertainty_kind=UncertaintyKind.CLAUSE_BOUNDARY_UNCERTAIN,
                    related_refs=(clause_id,),
                    reason="competing clause boundaries detected across dictum candidates",
                    confidence=0.38,
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.UNCERTAINTY_CUE,
                source_ref_ids=(clause_id,),
                supports_dimensions=("clause_boundary",),
                unresolved=True,
                route_class="shared",
                reason="competing clause boundaries preserved as uncertainty cue",
            )

    if dictum_bundle.conflicts:
        ambiguity_reasons.append("dictum_conflicts_present")
    if dictum_bundle.unknowns:
        ambiguity_reasons.append("dictum_unknowns_present")
    if dictum_bundle.ambiguities:
        ambiguity_reasons.extend(amb.reason for amb in dictum_bundle.ambiguities)

    if surface is None:
        low_coverage_reasons.append(G01CoverageCode.SURFACE_NOT_PROVIDED)
    if not source_anchors:
        low_coverage_reasons.append(G01CoverageCode.SOURCE_ANCHORS_SPARSE)
    if not operator_carriers:
        low_coverage_reasons.append(G01CoverageCode.OPERATOR_CARRIERS_SPARSE)
    if memory_anchor_ref is None:
        low_coverage_reasons.append(G01CoverageCode.M03_ANCHOR_NOT_PROVIDED)
    if cooperation_anchor_ref is None:
        low_coverage_reasons.append(G01CoverageCode.O03_ANCHOR_NOT_PROVIDED)

    low_coverage_mode = bool(low_coverage_reasons)
    reversible_span_mapping_present = bool(surface and surface.reversible_span_map_present)

    bundle = GroundedSemanticBundle(
        source_dictum_ref=dictum_bundle.source_lexical_grounding_ref,
        source_syntax_ref=dictum_bundle.source_syntax_ref,
        source_surface_ref=dictum_bundle.source_surface_ref,
        source_modus_ref=source_refs.source_modus_ref,
        source_modus_ref_kind=source_refs.source_modus_ref_kind,
        source_modus_lineage_ref=source_refs.source_modus_lineage_ref,
        source_discourse_update_ref=source_refs.source_discourse_update_ref,
        source_discourse_update_ref_kind=source_refs.source_discourse_update_ref_kind,
        source_discourse_update_lineage_ref=source_refs.source_discourse_update_lineage_ref,
        linked_dictum_candidate_ids=tuple(candidate.dictum_candidate_id for candidate in dictum_bundle.dictum_candidates),
        linked_modus_record_ids=tuple(record.record_id for record in modus_bundle.hypothesis_records) if modus_bundle is not None else (),
        linked_update_proposal_ids=tuple(proposal.proposal_id for proposal in discourse_bundle.update_proposals) if discourse_bundle is not None else (),
        substrate_units=tuple(substrate_units),
        phrase_scaffolds=tuple(phrase_scaffolds),
        operator_carriers=tuple(operator_carriers),
        dictum_carriers=tuple(dictum_carriers),
        modus_carriers=tuple(modus_carriers),
        source_anchors=tuple(source_anchors),
        uncertainty_markers=tuple(uncertainty_markers),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        low_coverage_mode=low_coverage_mode,
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage_reasons)),
        normative_l05_l06_route_active=normative_l05_l06_route_active,
        legacy_surface_cue_fallback_used=legacy_surface_cue_fallback_used,
        legacy_surface_cue_path_not_normative=False,
        l04_only_input_not_equivalent_to_l05_l06_route=False,
        discourse_update_not_inferred_from_surface_when_l06_available=discourse_update_not_inferred_from_surface_when_l06_available,
        l06_blocked_update_present=l06_blocked_update_present,
        l06_guarded_continue_present=l06_guarded_continue_present,
        no_final_semantic_resolution=True,
        reason="g01 grounded semantic scaffold generated via normative l05+l06 intake with bounded restrictions",
        evidence_records=tuple(evidence_records),
    )
    gate = evaluate_grounded_semantic_downstream_gate(bundle)
    source_lineage = _compose_source_lineage(
        dictum_bundle=dictum_bundle,
        source_refs=source_refs,
        modus_bundle=modus_bundle,
        discourse_bundle=discourse_bundle,
        dictum_lineage=dictum_lineage,
        modus_lineage=modus_lineage,
        discourse_lineage=discourse_lineage,
        memory_anchor_ref=memory_anchor_ref,
        cooperation_anchor_ref=cooperation_anchor_ref,
    )
    telemetry = build_grounded_semantic_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        reversible_span_mapping_present=reversible_span_mapping_present,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="l04 substrate scaffold combined with typed l05 force/addressivity and l06 update/repair signals",
    )
    confidence = _estimate_result_confidence(bundle)
    partial_known = bool(bundle.uncertainty_markers or bundle.low_coverage_mode or bundle.ambiguity_reasons)
    partial_known_reason = (
        "; ".join(bundle.ambiguity_reasons)
        if bundle.ambiguity_reasons
        else ("; ".join(bundle.low_coverage_reasons) if bundle.low_coverage_reasons else None)
    )
    abstain = not gate.accepted
    abstain_reason = None if gate.accepted else gate.reason
    return GroundedSemanticResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_final_semantic_resolution=True,
    )


def grounded_semantic_result_to_payload(result: GroundedSemanticResult) -> dict[str, object]:
    return grounded_semantic_result_snapshot(result)


def persist_grounded_semantic_result_via_f01(
    *,
    result: GroundedSemanticResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("g01-grounded-semantic-substrate",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"grounded-semantic-step-{transition_id}",
            "grounded_semantic_snapshot": grounded_semantic_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_dictum_input(
    dictum_result_or_bundle: DictumCandidateResult | DictumCandidateBundle,
) -> tuple[DictumCandidateBundle, tuple[str, ...]]:
    if isinstance(dictum_result_or_bundle, DictumCandidateResult):
        return dictum_result_or_bundle.bundle, dictum_result_or_bundle.telemetry.source_lineage
    if isinstance(dictum_result_or_bundle, DictumCandidateBundle):
        return dictum_result_or_bundle, ()
    raise TypeError(
        "build_grounded_semantic_substrate requires DictumCandidateResult or DictumCandidateBundle"
    )


def _extract_optional_surface(
    utterance_surface: UtteranceSurface | UtteranceSurfaceResult | None,
) -> UtteranceSurface | None:
    if utterance_surface is None:
        return None
    if isinstance(utterance_surface, UtteranceSurface):
        return utterance_surface
    if isinstance(utterance_surface, UtteranceSurfaceResult):
        return utterance_surface.surface
    raise TypeError("utterance_surface must be UtteranceSurface or UtteranceSurfaceResult when provided")


def _extract_optional_modus_input(
    modus_result_or_bundle: ModusHypothesisResult | ModusHypothesisBundle | None,
) -> tuple[ModusHypothesisBundle | None, tuple[str, ...]]:
    if modus_result_or_bundle is None:
        return None, ()
    if isinstance(modus_result_or_bundle, ModusHypothesisResult):
        return modus_result_or_bundle.bundle, modus_result_or_bundle.telemetry.source_lineage
    if isinstance(modus_result_or_bundle, ModusHypothesisBundle):
        return modus_result_or_bundle, ()
    raise TypeError(
        "modus_hypotheses_result_or_bundle must be typed ModusHypothesisResult/ModusHypothesisBundle when provided"
    )


def _extract_optional_discourse_update_input(
    discourse_update_result_or_bundle: DiscourseUpdateResult | DiscourseUpdateBundle | None,
) -> tuple[DiscourseUpdateBundle | None, tuple[str, ...]]:
    if discourse_update_result_or_bundle is None:
        return None, ()
    if isinstance(discourse_update_result_or_bundle, DiscourseUpdateResult):
        return discourse_update_result_or_bundle.bundle, discourse_update_result_or_bundle.telemetry.source_lineage
    if isinstance(discourse_update_result_or_bundle, DiscourseUpdateBundle):
        return discourse_update_result_or_bundle, ()
    raise TypeError(
        "discourse_update_result_or_bundle must be typed DiscourseUpdateResult/DiscourseUpdateBundle when provided"
    )


def _is_normative_binding_compatible(
    *,
    dictum_bundle: DictumCandidateBundle,
    modus_bundle: ModusHypothesisBundle,
    discourse_bundle: DiscourseUpdateBundle,
) -> bool:
    return _normative_binding_failure_code(
        dictum_bundle=dictum_bundle,
        modus_bundle=modus_bundle,
        discourse_bundle=discourse_bundle,
    ) is None


def _normative_binding_failure_code(
    *,
    dictum_bundle: DictumCandidateBundle,
    modus_bundle: ModusHypothesisBundle,
    discourse_bundle: DiscourseUpdateBundle,
) -> G01NormativeBindingFailureCode | None:
    dictum_ids = {candidate.dictum_candidate_id for candidate in dictum_bundle.dictum_candidates}
    modus_record_ids = {record.record_id for record in modus_bundle.hypothesis_records}
    if not dictum_ids:
        return G01NormativeBindingFailureCode.EMPTY_DICTUM_CANDIDATE_IDS
    if not modus_record_ids:
        return G01NormativeBindingFailureCode.EMPTY_MODUS_RECORD_IDS
    if not discourse_bundle.update_proposals:
        return G01NormativeBindingFailureCode.EMPTY_DISCOURSE_UPDATE_PROPOSALS
    if any(not proposal.acceptance_required for proposal in discourse_bundle.update_proposals):
        return G01NormativeBindingFailureCode.L06_PROPOSAL_ACCEPTANCE_REQUIRED_FALSE
    if any(
        proposal.acceptance_status is AcceptanceStatus.ACCEPTED
        for proposal in discourse_bundle.update_proposals
    ):
        return G01NormativeBindingFailureCode.L06_PROPOSAL_ACCEPTANCE_STATUS_ACCEPTED
    if modus_bundle.source_dictum_ref != dictum_bundle.source_lexical_grounding_ref:
        return G01NormativeBindingFailureCode.L05_SOURCE_DICTUM_REF_MISMATCH
    if discourse_bundle.source_modus_lineage_ref != modus_bundle.source_dictum_ref:
        return G01NormativeBindingFailureCode.L06_SOURCE_MODUS_LINEAGE_REF_MISMATCH
    if not set(modus_bundle.linked_dictum_candidate_ids).intersection(dictum_ids):
        return G01NormativeBindingFailureCode.L05_LINKED_DICTUM_IDS_NO_INTERSECTION
    proposal_source_record_ids = {
        proposal.source_record_ids[0]
        for proposal in discourse_bundle.update_proposals
        if proposal.source_record_ids
    }
    if not proposal_source_record_ids:
        return G01NormativeBindingFailureCode.L06_PROPOSAL_SOURCE_RECORD_IDS_EMPTY
    if not proposal_source_record_ids.issubset(modus_record_ids):
        return G01NormativeBindingFailureCode.L06_PROPOSAL_SOURCE_RECORD_IDS_NOT_SUBSET_L05
    continuation_source_record_ids = {
        continuation.source_record_id for continuation in discourse_bundle.continuation_states
    }
    if continuation_source_record_ids and not continuation_source_record_ids.issubset(
        modus_record_ids
    ):
        return (
            G01NormativeBindingFailureCode.L06_CONTINUATION_SOURCE_RECORD_IDS_NOT_SUBSET_L05
        )
    if discourse_bundle.linked_modus_record_ids and not set(
        discourse_bundle.linked_modus_record_ids
    ).issubset(modus_record_ids):
        return G01NormativeBindingFailureCode.L06_LINKED_MODUS_RECORD_IDS_NOT_SUBSET_L05
    return None


def _derive_source_refs(
    *,
    modus_bundle: ModusHypothesisBundle | None,
    discourse_bundle: DiscourseUpdateBundle | None,
) -> _G01SourceRefs:
    if modus_bundle is None or discourse_bundle is None:
        return _G01SourceRefs(
            source_modus_ref=None,
            source_modus_ref_kind="not_bound",
            source_modus_lineage_ref=None,
            source_discourse_update_ref=None,
            source_discourse_update_ref_kind="not_bound",
            source_discourse_update_lineage_ref=None,
        )
    return _G01SourceRefs(
        source_modus_ref=_derive_l05_bundle_ref(modus_bundle),
        source_modus_ref_kind="phase_native_derived_ref",
        source_modus_lineage_ref=modus_bundle.source_dictum_ref,
        source_discourse_update_ref=_derive_l06_bundle_ref(discourse_bundle),
        source_discourse_update_ref_kind="phase_native_derived_ref",
        source_discourse_update_lineage_ref=discourse_bundle.source_modus_lineage_ref,
    )


def _compose_source_lineage(
    *,
    dictum_bundle: DictumCandidateBundle,
    source_refs: _G01SourceRefs,
    modus_bundle: ModusHypothesisBundle | None,
    discourse_bundle: DiscourseUpdateBundle | None,
    dictum_lineage: tuple[str, ...],
    modus_lineage: tuple[str, ...],
    discourse_lineage: tuple[str, ...],
    memory_anchor_ref: str | None,
    cooperation_anchor_ref: str | None,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *((source_refs.source_modus_ref,) if source_refs.source_modus_ref else ()),
                *((source_refs.source_modus_lineage_ref,) if source_refs.source_modus_lineage_ref else ()),
                *((source_refs.source_discourse_update_ref,) if source_refs.source_discourse_update_ref else ()),
                *((source_refs.source_discourse_update_lineage_ref,) if source_refs.source_discourse_update_lineage_ref else ()),
                dictum_bundle.source_lexical_grounding_ref,
                dictum_bundle.source_syntax_ref,
                *((modus_bundle.source_dictum_ref,) if modus_bundle is not None else ()),
                *((discourse_bundle.source_modus_ref,) if discourse_bundle is not None else ()),
                *dictum_lineage,
                *modus_lineage,
                *discourse_lineage,
                *((f"m03:{memory_anchor_ref}",) if memory_anchor_ref else ()),
                *((f"o03:{cooperation_anchor_ref}",) if cooperation_anchor_ref else ()),
            )
        )
    )


def _derive_l05_bundle_ref(modus_bundle: ModusHypothesisBundle) -> str:
    head = modus_bundle.hypothesis_records[0].record_id if modus_bundle.hypothesis_records else "none"
    return f"l05.bundle:{head}:n={len(modus_bundle.hypothesis_records)}"


def _derive_l06_bundle_ref(discourse_bundle: DiscourseUpdateBundle) -> str:
    head = discourse_bundle.update_proposals[0].proposal_id if discourse_bundle.update_proposals else "none"
    return f"l06.bundle:{head}:p={len(discourse_bundle.update_proposals)}:r={len(discourse_bundle.repair_triggers)}:c={len(discourse_bundle.continuation_states)}"


def _register_normative_l05_l06_cues(
    *,
    dictum_bundle: DictumCandidateBundle,
    dictum_span_by_id: dict[str, tuple[int, int]],
    modus_bundle: ModusHypothesisBundle,
    discourse_bundle: DiscourseUpdateBundle,
    source_anchors: list[SourceAnchor],
    operator_carriers: list[OperatorCarrier],
    modus_carriers: list[ModusCarrier],
    uncertainty_markers: list[UncertaintyMarker],
    evidence_records: list[G01EvidenceRecord],
    start_anchor_index: int,
    start_carrier_index: int,
    start_uncertainty_index: int,
    start_evidence_index: int,
) -> tuple[int, int, int, int, bool, bool]:
    anchor_index = start_anchor_index
    carrier_index = start_carrier_index
    uncertainty_index = start_uncertainty_index
    evidence_index = start_evidence_index
    l06_blocked_update_present = False
    l06_guarded_continue_present = False

    record_by_id = {record.record_id: record for record in modus_bundle.hypothesis_records}
    proposal_by_record_id: dict[str, list[str]] = {}
    for proposal in discourse_bundle.update_proposals:
        if proposal.source_record_ids:
            proposal_by_record_id.setdefault(proposal.source_record_ids[0], []).append(proposal.proposal_id)

    for record in modus_bundle.hypothesis_records:
        anchor_span = dictum_span_by_id.get(record.source_dictum_candidate_id, (0, 0))
        evidence_kinds = {evidence.evidence_kind for evidence in record.evidence_records}
        has_force_evidence = ModusEvidenceKind.FORCE_CUE in evidence_kinds
        has_modality_evidence = ModusEvidenceKind.MODALITY_CUE in evidence_kinds
        has_quotation_evidence = ModusEvidenceKind.QUOTATION_CUE in evidence_kinds
        has_addressivity_evidence = ModusEvidenceKind.ADDRESSIVITY_CUE in evidence_kinds
        force_alternatives_must_read = (
            L05CautionCode.FORCE_ALTERNATIVES_MUST_BE_READ in record.downstream_cautions
        )
        sorted_hypotheses = sorted(
            record.illocution_hypotheses,
            key=lambda hypothesis: hypothesis.confidence_weight,
            reverse=True,
        )
        primary = sorted_hypotheses[0] if sorted_hypotheses else None
        primary_kind = primary.illocution_kind if primary is not None else IllocutionKind.UNKNOWN_FORCE_CANDIDATE
        evidence_refs = (record.record_id,) if primary is None else (record.record_id, *primary.evidence_refs)
        carrier_index += 1
        modus_carriers.append(
            ModusCarrier(
                carrier_id=f"carrier-{carrier_index}",
                dictum_candidate_id=record.source_dictum_candidate_id,
                stance_kind=f"{CarrierKind.MODUS_STANCE.value}:l05:{primary_kind.value}",
                evidence_refs=evidence_refs,
                unresolved=record.uncertainty_entropy >= 0.7 or (primary.unresolved if primary is not None else True),
                confidence=min(0.92, max(0.18, record.confidence)),
                provenance="g01 normative modus carrier from l05 hypothesis topology",
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.NORMATIVE_L05_CUE,
            source_ref_ids=(record.record_id, record.source_dictum_candidate_id),
            supports_dimensions=("modus_force", "addressivity"),
            unresolved=record.uncertainty_entropy >= 0.7,
            route_class="normative",
            reason="typed l05 record bound into g01 normative route",
        )

        if primary_kind is IllocutionKind.INTERROGATIVE_CANDIDATE and has_force_evidence:
            carrier_index += 1
            operator_carriers.append(
                OperatorCarrier(
                    operator_id=f"op-{carrier_index}",
                    operator_kind=OperatorKind.INTERROGATION,
                    carrier_unit_ids=(),
                    scope_anchor_refs=(record.source_dictum_candidate_id,),
                    scope_uncertain=record.uncertainty_entropy >= 0.6,
                    confidence=min(0.88, max(0.2, record.confidence)),
                    provenance="g01 interrogation carrier from l05 illocution hypotheses",
                )
            )

        if record.modality_profile.modality_markers and has_modality_evidence:
            carrier_index += 1
            operator_carriers.append(
                OperatorCarrier(
                    operator_id=f"op-{carrier_index}",
                    operator_kind=OperatorKind.MODALITY,
                    carrier_unit_ids=(),
                    scope_anchor_refs=(record.source_dictum_candidate_id,),
                    scope_uncertain=record.modality_profile.unresolved,
                    confidence=min(0.84, max(0.2, record.confidence)),
                    provenance="g01 modality carrier from l05 modality profile",
                )
            )
        elif record.modality_profile.modality_markers and not has_modality_evidence:
            uncertainty_index += 1
            uncertainty_markers.append(
                UncertaintyMarker(
                    marker_id=f"uncertainty-{uncertainty_index}",
                    uncertainty_kind=UncertaintyKind.OPERATOR_SCOPE_UNCERTAIN,
                    related_refs=(record.record_id,),
                    reason="l05 modality markers present without modality evidence record",
                    confidence=0.42,
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.NORMATIVE_L05_CUE,
                source_ref_ids=(record.record_id,),
                supports_dimensions=("modality_evidence_gap",),
                unresolved=True,
                route_class="normative",
                reason="l05 modality evidence gap degraded g01 normative intake",
            )

        if record.quoted_speech_state.quote_or_echo_present and has_quotation_evidence:
            anchor_index += 1
            source_anchors.append(
                SourceAnchor(
                    anchor_id=f"source-{anchor_index}",
                    anchor_kind=SourceAnchorKind.QUOTE_BOUNDARY,
                    span_start=anchor_span[0],
                    span_end=anchor_span[1],
                    marker_text="l05:quoted_or_echoic",
                    unresolved=record.quoted_speech_state.unresolved_source_scope,
                    confidence=min(0.86, max(0.2, record.confidence)),
                    provenance="g01 quote anchor from l05 quoted speech state",
                )
            )
            carrier_index += 1
            operator_carriers.append(
                OperatorCarrier(
                    operator_id=f"op-{carrier_index}",
                    operator_kind=OperatorKind.QUOTATION,
                    carrier_unit_ids=(),
                    scope_anchor_refs=(f"source-{anchor_index}",),
                    scope_uncertain=record.quoted_speech_state.unresolved_source_scope,
                    confidence=min(0.86, max(0.2, record.confidence)),
                    provenance="g01 quotation carrier from l05 quoted speech state",
                )
            )
        elif record.quoted_speech_state.quote_or_echo_present and not has_quotation_evidence:
            uncertainty_index += 1
            uncertainty_markers.append(
                UncertaintyMarker(
                    marker_id=f"uncertainty-{uncertainty_index}",
                    uncertainty_kind=UncertaintyKind.SOURCE_SCOPE_UNCERTAIN,
                    related_refs=(record.record_id, record.source_dictum_candidate_id),
                    reason="l05 quote state present without quotation evidence record",
                    confidence=0.44,
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.NORMATIVE_L05_CUE,
                source_ref_ids=(record.record_id, record.source_dictum_candidate_id),
                supports_dimensions=("quotation_evidence_gap",),
                unresolved=True,
                route_class="normative",
                reason="l05 quotation evidence gap degraded g01 normative intake",
            )

        sorted_targets = sorted(
            record.addressivity_hypotheses,
            key=lambda addressivity: addressivity.confidence_weight,
            reverse=True,
        )
        primary_target = sorted_targets[0] if sorted_targets else None
        if primary_target is not None and has_addressivity_evidence:
            if primary_target.addressivity_kind is AddressivityKind.QUOTED_SPEAKER:
                anchor_kind = SourceAnchorKind.QUOTE_BOUNDARY
            elif primary_target.addressivity_kind is AddressivityKind.REPORTED_PARTICIPANT:
                anchor_kind = SourceAnchorKind.REPORTED_SPEECH
            elif primary_target.addressivity_kind is AddressivityKind.UNKNOWN_TARGET:
                anchor_kind = SourceAnchorKind.UNKNOWN
            else:
                anchor_kind = SourceAnchorKind.SPEAKER_MARKER
            anchor_index += 1
            source_anchors.append(
                SourceAnchor(
                    anchor_id=f"source-{anchor_index}",
                    anchor_kind=anchor_kind,
                    span_start=anchor_span[0],
                    span_end=anchor_span[1],
                    marker_text=f"l05:addressivity:{primary_target.addressivity_kind.value}",
                    unresolved=primary_target.unresolved,
                    confidence=min(0.86, max(0.2, primary_target.confidence_weight)),
                    provenance="g01 source anchor from l05 addressivity hypotheses",
                )
            )
        elif primary_target is not None and not has_addressivity_evidence:
            uncertainty_index += 1
            uncertainty_markers.append(
                UncertaintyMarker(
                    marker_id=f"uncertainty-{uncertainty_index}",
                    uncertainty_kind=UncertaintyKind.REFERENT_UNRESOLVED,
                    related_refs=(record.record_id, record.source_dictum_candidate_id),
                    reason="l05 addressivity hypothesis present without addressivity evidence record",
                    confidence=0.41,
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.NORMATIVE_L05_CUE,
                source_ref_ids=(record.record_id, record.source_dictum_candidate_id),
                supports_dimensions=("addressivity_evidence_gap",),
                unresolved=True,
                route_class="normative",
                reason="l05 addressivity evidence gap degraded g01 normative intake",
            )

        if record.uncertainty_entropy >= 0.72 or force_alternatives_must_read:
            uncertainty_index += 1
            uncertainty_markers.append(
                UncertaintyMarker(
                    marker_id=f"uncertainty-{uncertainty_index}",
                    uncertainty_kind=UncertaintyKind.OPERATOR_SCOPE_UNCERTAIN,
                    related_refs=(record.record_id,),
                    reason=(
                        "l05 uncertainty entropy remains high for g01 grounding"
                        if record.uncertainty_entropy >= 0.72
                        else "l05 force alternatives caution requires uncertainty carry-through"
                    ),
                    confidence=min(0.78, max(0.2, record.uncertainty_entropy)),
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.UNCERTAINTY_CUE,
                source_ref_ids=(record.record_id,),
                supports_dimensions=("entropy_pressure",),
                unresolved=True,
                route_class="normative",
                reason="l05 high entropy preserved as explicit uncertainty cue",
            )

    proposal_ids_by_continuation = {
        continuation.source_record_id: proposal_by_record_id.get(continuation.source_record_id, ())
        for continuation in discourse_bundle.continuation_states
    }
    for continuation in discourse_bundle.continuation_states:
        if continuation.continuation_status is ContinuationStatus.BLOCKED_PENDING_REPAIR:
            l06_blocked_update_present = True
            uncertainty_index += 1
            uncertainty_markers.append(
                UncertaintyMarker(
                    marker_id=f"uncertainty-{uncertainty_index}",
                    uncertainty_kind=UncertaintyKind.SOURCE_SCOPE_UNCERTAIN,
                    related_refs=tuple(
                        dict.fromkeys(
                            (
                                continuation.continuation_id,
                                *proposal_ids_by_continuation.get(continuation.source_record_id, ()),
                                *continuation.localized_repair_refs,
                            )
                        )
                    ),
                    reason="l06 blocked update pending localized repair",
                    confidence=0.52,
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.NORMATIVE_L06_CUE,
                source_ref_ids=tuple(
                    dict.fromkeys(
                        (
                            continuation.continuation_id,
                            *proposal_ids_by_continuation.get(continuation.source_record_id, ()),
                            *continuation.localized_repair_refs,
                        )
                    )
                ),
                supports_dimensions=("discourse_update_continuation",),
                unresolved=True,
                route_class="normative",
                reason="l06 blocked continuation propagated into g01 normative topology",
            )
        elif continuation.continuation_status is ContinuationStatus.GUARDED_CONTINUE:
            l06_guarded_continue_present = True
            uncertainty_index += 1
            uncertainty_markers.append(
                UncertaintyMarker(
                    marker_id=f"uncertainty-{uncertainty_index}",
                    uncertainty_kind=UncertaintyKind.OPERATOR_SCOPE_UNCERTAIN,
                    related_refs=tuple(
                        dict.fromkeys(
                            (
                                continuation.continuation_id,
                                *proposal_ids_by_continuation.get(continuation.source_record_id, ()),
                                *continuation.localized_repair_refs,
                            )
                        )
                    ),
                    reason="l06 guarded continuation requires limits before strong downstream use",
                    confidence=0.48,
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.NORMATIVE_L06_CUE,
                source_ref_ids=tuple(
                    dict.fromkeys(
                        (
                            continuation.continuation_id,
                            *proposal_ids_by_continuation.get(continuation.source_record_id, ()),
                            *continuation.localized_repair_refs,
                        )
                    )
                ),
                supports_dimensions=("discourse_update_continuation",),
                unresolved=True,
                route_class="normative",
                reason="l06 guarded continuation propagated into g01 normative topology",
            )

    for repair in discourse_bundle.repair_triggers:
        if repair.repair_class is RepairClass.REFERENCE_REPAIR:
            kind = UncertaintyKind.REFERENT_UNRESOLVED
        elif repair.repair_class is RepairClass.SCOPE_REPAIR:
            kind = UncertaintyKind.OPERATOR_SCOPE_UNCERTAIN
        elif repair.repair_class is RepairClass.POLARITY_REPAIR:
            kind = UncertaintyKind.OPERATOR_SCOPE_UNCERTAIN
        elif repair.repair_class is RepairClass.FORCE_REPAIR:
            kind = UncertaintyKind.SOURCE_SCOPE_UNCERTAIN
        else:
            kind = UncertaintyKind.ATTACHMENT_AMBIGUOUS
        uncertainty_index += 1
        uncertainty_markers.append(
            UncertaintyMarker(
                marker_id=f"uncertainty-{uncertainty_index}",
                uncertainty_kind=kind,
                related_refs=tuple(dict.fromkeys((repair.repair_id, *repair.localized_ref_ids))),
                reason=f"l06 localized repair pending: {repair.localized_trouble_source}",
                confidence=0.47,
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.NORMATIVE_L06_CUE,
            source_ref_ids=tuple(dict.fromkeys((repair.repair_id, *repair.localized_ref_ids))),
            supports_dimensions=("repair_localization",),
            unresolved=True,
            route_class="normative",
            reason=f"l06 repair class propagated to g01 uncertainty topology:{repair.repair_class.value}",
        )

    for proposal in discourse_bundle.update_proposals:
        if proposal.proposal_type is ProposalType.QUESTION_INTERPRETATION_UPDATE:
            carrier_index += 1
            operator_carriers.append(
                OperatorCarrier(
                    operator_id=f"op-{carrier_index}",
                    operator_kind=OperatorKind.INTERROGATION,
                    carrier_unit_ids=(),
                    scope_anchor_refs=(proposal.proposal_id,),
                    scope_uncertain=True,
                    confidence=0.52,
                    provenance="g01 interrogation carrier from l06 proposal topology",
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.NORMATIVE_L06_CUE,
                source_ref_ids=(proposal.proposal_id,),
                supports_dimensions=("update_proposal_topology",),
                unresolved=True,
                route_class="normative",
                reason="l06 question interpretation proposal emitted interrogation operator",
            )
        elif proposal.proposal_type in {
            ProposalType.REPORTED_CONTENT_UPDATE,
            ProposalType.QUOTED_CONTENT_UPDATE,
            ProposalType.ECHOIC_CONTENT_UPDATE,
        }:
            carrier_index += 1
            operator_carriers.append(
                OperatorCarrier(
                    operator_id=f"op-{carrier_index}",
                    operator_kind=OperatorKind.QUOTATION,
                    carrier_unit_ids=(),
                    scope_anchor_refs=(proposal.proposal_id,),
                    scope_uncertain=True,
                    confidence=0.5,
                    provenance="g01 quotation carrier from l06 proposal topology",
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.NORMATIVE_L06_CUE,
                source_ref_ids=(proposal.proposal_id,),
                supports_dimensions=("update_proposal_topology", "source_mode"),
                unresolved=True,
                route_class="normative",
                reason="l06 reported/quoted proposal emitted quotation operator",
            )

    return (
        anchor_index,
        carrier_index,
        uncertainty_index,
        evidence_index,
        l06_blocked_update_present,
        l06_guarded_continue_present,
    )


def _register_surface_cues(
    *,
    surface: UtteranceSurface | None,
    linked_dictum_ids: tuple[str, ...],
    source_anchors: list[SourceAnchor],
    operator_carriers: list[OperatorCarrier],
    modus_carriers: list[ModusCarrier],
    uncertainty_markers: list[UncertaintyMarker],
    evidence_records: list[G01EvidenceRecord],
    start_anchor_index: int,
    start_carrier_index: int,
    start_uncertainty_index: int,
    start_evidence_index: int,
) -> tuple[int, int, int, int]:
    if surface is None:
        return start_anchor_index, start_carrier_index, start_uncertainty_index, start_evidence_index

    anchor_index = start_anchor_index
    carrier_index = start_carrier_index
    uncertainty_index = start_uncertainty_index
    evidence_index = start_evidence_index
    raw_text = surface.raw_text

    for quote in surface.quotes:
        anchor_index += 1
        source_anchors.append(
            SourceAnchor(
                anchor_id=f"source-{anchor_index}",
                anchor_kind=SourceAnchorKind.QUOTE_BOUNDARY,
                span_start=quote.raw_span.start,
                span_end=quote.raw_span.end,
                marker_text=quote.raw_span.raw_text,
                unresolved=False,
                confidence=quote.confidence,
                provenance="g01 source anchor from l01 quoted span",
            )
        )
        carrier_index += 1
        operator_carriers.append(
            OperatorCarrier(
                operator_id=f"op-{carrier_index}",
                operator_kind=OperatorKind.QUOTATION,
                carrier_unit_ids=(),
                scope_anchor_refs=(f"source-{anchor_index}",),
                scope_uncertain=False,
                confidence=quote.confidence,
                provenance="g01 quotation operator carrier from l01 quote boundaries",
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
            source_ref_ids=(f"source-{anchor_index}",),
            supports_dimensions=("source_mode", "quotation"),
            unresolved=False,
            route_class="compatibility",
            reason="legacy compatibility quote boundary cue from l01 surface",
        )

    for pattern, kind in (
        (_MODAL_CUE_PATTERN, OperatorKind.MODALITY),
        (_COORDINATION_CUE_PATTERN, OperatorKind.COORDINATION),
        (_CONDITIONAL_CUE_PATTERN, OperatorKind.CONDITIONAL),
        (_STANCE_PARTICLE_PATTERN, OperatorKind.DISCOURSE_PARTICLE),
    ):
        for match in pattern.finditer(raw_text):
            carrier_index += 1
            operator_carriers.append(
                OperatorCarrier(
                    operator_id=f"op-{carrier_index}",
                    operator_kind=kind,
                    carrier_unit_ids=(),
                    scope_anchor_refs=linked_dictum_ids[:1],
                    scope_uncertain=False,
                    confidence=0.52,
                    provenance="g01 operator carrier from surface lexical cue",
                )
            )
            evidence_index = _append_g01_evidence(
                evidence_records=evidence_records,
                evidence_index=evidence_index,
                evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
                source_ref_ids=(f"surface-cue:{match.group(0).lower()}",),
                supports_dimensions=("operator_projection",),
                unresolved=False,
                route_class="compatibility",
                reason=f"legacy compatibility operator cue:{kind.value}",
            )
            if kind in {OperatorKind.MODALITY, OperatorKind.DISCOURSE_PARTICLE}:
                carrier_index += 1
                modus_carriers.append(
                    ModusCarrier(
                        carrier_id=f"carrier-{carrier_index}",
                        dictum_candidate_id=linked_dictum_ids[0] if linked_dictum_ids else "none",
                        stance_kind=CarrierKind.MODUS_STANCE.value + f":{kind.value}",
                        evidence_refs=(f"surface-cue:{match.group(0).lower()}",),
                        unresolved=True,
                        confidence=0.49,
                        provenance="g01 modus carrier from stance/modality cue",
                    )
                )
                evidence_index = _append_g01_evidence(
                    evidence_records=evidence_records,
                    evidence_index=evidence_index,
                    evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
                    source_ref_ids=(f"surface-cue:{match.group(0).lower()}",),
                    supports_dimensions=("modus_stance",),
                    unresolved=True,
                    route_class="compatibility",
                    reason="legacy compatibility modality/stance cue into modus carrier",
                )

    for match in _REPORT_CUE_PATTERN.finditer(raw_text):
        anchor_index += 1
        source_anchors.append(
            SourceAnchor(
                anchor_id=f"source-{anchor_index}",
                anchor_kind=SourceAnchorKind.REPORTED_SPEECH,
                span_start=match.start(),
                span_end=match.end(),
                marker_text=match.group(0),
                unresolved=True,
                confidence=0.54,
                provenance="g01 reported-speech cue anchor from surface text",
            )
        )
        carrier_index += 1
        modus_carriers.append(
            ModusCarrier(
                carrier_id=f"carrier-{carrier_index}",
                dictum_candidate_id=linked_dictum_ids[0] if linked_dictum_ids else "none",
                stance_kind=CarrierKind.MODUS_STANCE.value + ":reported_speech",
                evidence_refs=(f"source-{anchor_index}",),
                unresolved=True,
                confidence=0.5,
                provenance="g01 modus carrier from report cue",
            )
        )
        uncertainty_index += 1
        uncertainty_markers.append(
            UncertaintyMarker(
                marker_id=f"uncertainty-{uncertainty_index}",
                uncertainty_kind=UncertaintyKind.SOURCE_SCOPE_UNCERTAIN,
                related_refs=(f"source-{anchor_index}",),
                reason="reported speech cue without final source resolution",
                confidence=0.44,
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
            source_ref_ids=(f"source-{anchor_index}",),
            supports_dimensions=("source_mode", "reporting"),
            unresolved=True,
            route_class="compatibility",
            reason="legacy compatibility report cue anchors unresolved source scope",
        )

    for match in _SPEAKER_PATTERN.finditer(raw_text):
        anchor_index += 1
        source_anchors.append(
            SourceAnchor(
                anchor_id=f"source-{anchor_index}",
                anchor_kind=SourceAnchorKind.SPEAKER_MARKER,
                span_start=match.start(),
                span_end=match.end(),
                marker_text=match.group(0),
                unresolved=True,
                confidence=0.5,
                provenance="g01 speaker marker from surface cue",
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
            source_ref_ids=(f"source-{anchor_index}",),
            supports_dimensions=("source_mode",),
            unresolved=True,
            route_class="compatibility",
            reason="legacy compatibility speaker cue anchor",
        )

    for match in _DEIXIS_PATTERN.finditer(raw_text):
        anchor_index += 1
        source_anchors.append(
            SourceAnchor(
                anchor_id=f"source-{anchor_index}",
                anchor_kind=SourceAnchorKind.DEIXIS_PLACEHOLDER,
                span_start=match.start(),
                span_end=match.end(),
                marker_text=match.group(0),
                unresolved=True,
                confidence=0.42,
                provenance="g01 deixis placeholder anchor from surface cue",
            )
        )
        uncertainty_index += 1
        uncertainty_markers.append(
            UncertaintyMarker(
                marker_id=f"uncertainty-{uncertainty_index}",
                uncertainty_kind=UncertaintyKind.REFERENT_UNRESOLVED,
                related_refs=(f"source-{anchor_index}",),
                reason="deictic cue preserved as unresolved placeholder",
                confidence=0.38,
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
            source_ref_ids=(f"source-{anchor_index}",),
            supports_dimensions=("deixis_placeholder",),
            unresolved=True,
            route_class="compatibility",
            reason="legacy compatibility deixis cue preserved as unresolved placeholder",
        )

    if "?" in raw_text:
        carrier_index += 1
        operator_carriers.append(
            OperatorCarrier(
                operator_id=f"op-{carrier_index}",
                operator_kind=OperatorKind.INTERROGATION,
                carrier_unit_ids=(),
                scope_anchor_refs=linked_dictum_ids[:1],
                scope_uncertain=True,
                confidence=0.6,
                provenance="g01 interrogation operator from punctuation cue",
            )
        )
        carrier_index += 1
        modus_carriers.append(
            ModusCarrier(
                carrier_id=f"carrier-{carrier_index}",
                dictum_candidate_id=linked_dictum_ids[0] if linked_dictum_ids else "none",
                stance_kind=CarrierKind.MODUS_STANCE.value + ":interrogative",
                evidence_refs=("surface:question_mark",),
                unresolved=True,
                confidence=0.58,
                provenance="g01 modus carrier from interrogation cue",
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
            source_ref_ids=("surface:question_mark",),
            supports_dimensions=("interrogation", "modus_stance"),
            unresolved=True,
            route_class="compatibility",
            reason="legacy compatibility punctuation cue projects interrogative carrier",
        )

    if "..." in raw_text or "??" in raw_text:
        uncertainty_index += 1
        uncertainty_markers.append(
            UncertaintyMarker(
                marker_id=f"uncertainty-{uncertainty_index}",
                uncertainty_kind=UncertaintyKind.SURFACE_CORRUPTION_PRESENT,
                related_refs=("surface:noisy_punctuation",),
                reason="surface punctuation perturbation suggests corruption/noise",
                confidence=0.45,
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
            source_ref_ids=("surface:noisy_punctuation",),
            supports_dimensions=("surface_noise",),
            unresolved=True,
            route_class="compatibility",
            reason="legacy compatibility noisy punctuation cue",
        )

    for ambiguity in surface.ambiguities:
        mapped = _map_surface_uncertainty(ambiguity.ambiguity_kind.value)
        if mapped is None:
            continue
        uncertainty_index += 1
        uncertainty_markers.append(
            UncertaintyMarker(
                marker_id=f"uncertainty-{uncertainty_index}",
                uncertainty_kind=mapped,
                related_refs=(f"surface-span:{ambiguity.affected_span.start}:{ambiguity.affected_span.end}",),
                reason=ambiguity.reason,
                confidence=ambiguity.confidence,
            )
        )
        evidence_index = _append_g01_evidence(
            evidence_records=evidence_records,
            evidence_index=evidence_index,
            evidence_kind=G01EvidenceKind.LEGACY_SURFACE_CUE,
            source_ref_ids=(f"surface-span:{ambiguity.affected_span.start}:{ambiguity.affected_span.end}",),
            supports_dimensions=("surface_ambiguity",),
            unresolved=True,
            route_class="compatibility",
            reason=f"legacy compatibility surface ambiguity:{ambiguity.ambiguity_kind.value}",
        )

    return anchor_index, carrier_index, uncertainty_index, evidence_index


def _append_g01_evidence(
    *,
    evidence_records: list[G01EvidenceRecord],
    evidence_index: int,
    evidence_kind: G01EvidenceKind,
    source_ref_ids: tuple[str, ...],
    supports_dimensions: tuple[str, ...],
    unresolved: bool,
    route_class: str,
    reason: str,
) -> int:
    next_index = evidence_index + 1
    evidence_records.append(
        G01EvidenceRecord(
            evidence_id=f"g01-evidence-{next_index}",
            evidence_kind=evidence_kind,
            source_ref_ids=source_ref_ids,
            supports_dimensions=supports_dimensions,
            unresolved=unresolved,
            route_class=route_class,
            reason=reason,
        )
    )
    return next_index


def _operator_kind_from_scope_marker(marker_kind: str) -> OperatorKind:
    marker = marker_kind.lower()
    if "negation" in marker:
        return OperatorKind.NEGATION
    if "conditional" in marker:
        return OperatorKind.CONDITIONAL
    if "coord" in marker:
        return OperatorKind.COORDINATION
    return OperatorKind.DISCOURSE_PARTICLE


def _slice_text(raw_text: str, start: int, end: int) -> str:
    if not raw_text:
        return ""
    lo = max(0, start)
    hi = min(len(raw_text), max(lo, end))
    return raw_text[lo:hi]


def _map_surface_uncertainty(kind: str) -> UncertaintyKind | None:
    if "quote_boundary" in kind:
        return UncertaintyKind.SOURCE_SCOPE_UNCERTAIN
    if "terminal_boundary_missing" in kind:
        return UncertaintyKind.CLAUSE_BOUNDARY_UNCERTAIN
    if "boundary" in kind:
        return UncertaintyKind.TOKENIZATION_AMBIGUOUS
    if "noisy" in kind:
        return UncertaintyKind.SURFACE_CORRUPTION_PRESENT
    return None


def _estimate_result_confidence(bundle: GroundedSemanticBundle) -> float:
    base = 0.78
    if bundle.low_coverage_mode:
        base -= min(0.32, len(bundle.low_coverage_reasons) * 0.05)
    base -= min(0.26, len(bundle.uncertainty_markers) * 0.015)
    base -= min(0.2, len(bundle.ambiguity_reasons) * 0.02)
    if not bundle.phrase_scaffolds:
        base -= 0.2
    return max(0.1, min(0.92, round(base, 4)))


def _abstain_result(
    *,
    dictum_bundle: DictumCandidateBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> GroundedSemanticResult:
    source_refs = _derive_source_refs(modus_bundle=None, discourse_bundle=None)
    bundle = GroundedSemanticBundle(
        source_dictum_ref=dictum_bundle.source_lexical_grounding_ref,
        source_syntax_ref=dictum_bundle.source_syntax_ref,
        source_surface_ref=dictum_bundle.source_surface_ref,
        source_modus_ref=source_refs.source_modus_ref,
        source_modus_ref_kind=source_refs.source_modus_ref_kind,
        source_modus_lineage_ref=source_refs.source_modus_lineage_ref,
        source_discourse_update_ref=source_refs.source_discourse_update_ref,
        source_discourse_update_ref_kind=source_refs.source_discourse_update_ref_kind,
        source_discourse_update_lineage_ref=source_refs.source_discourse_update_lineage_ref,
        linked_dictum_candidate_ids=tuple(candidate.dictum_candidate_id for candidate in dictum_bundle.dictum_candidates),
        linked_modus_record_ids=(),
        linked_update_proposal_ids=(),
        substrate_units=(),
        phrase_scaffolds=(),
        operator_carriers=(),
        dictum_carriers=(),
        modus_carriers=(),
        source_anchors=(),
        uncertainty_markers=(
            UncertaintyMarker(
                marker_id="uncertainty-abstain",
                uncertainty_kind=UncertaintyKind.CLAUSE_BOUNDARY_UNCERTAIN,
                related_refs=(dictum_bundle.source_syntax_ref,),
                reason=reason,
                confidence=0.2,
            ),
        ),
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=(
            G01CoverageCode.ABSTAIN,
        ),
        normative_l05_l06_route_active=False,
        legacy_surface_cue_fallback_used=False,
        legacy_surface_cue_path_not_normative=False,
        l04_only_input_not_equivalent_to_l05_l06_route=False,
        discourse_update_not_inferred_from_surface_when_l06_available=False,
        l06_blocked_update_present=False,
        l06_guarded_continue_present=False,
        no_final_semantic_resolution=True,
        reason="g01 abstained due to insufficient l04 carriers",
    )
    gate = evaluate_grounded_semantic_downstream_gate(bundle)
    telemetry = build_grounded_semantic_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        reversible_span_mapping_present=False,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="invalid or empty l04 input -> g01 abstain",
    )
    return GroundedSemanticResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.1,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_semantic_resolution=True,
    )

from __future__ import annotations

import re
from collections import defaultdict

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.dictum_candidates.models import DictumCandidateBundle, DictumCandidateResult
from substrate.grounded_semantic.models import (
    AmbiguityState,
    CarrierKind,
    ChannelOrigin,
    DictumCarrier,
    GroundedSemanticBundle,
    GroundedSemanticResult,
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
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "g01.validate_typed_inputs",
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


def build_grounded_semantic_substrate(
    dictum_result_or_bundle: DictumCandidateResult | DictumCandidateBundle,
    utterance_surface: UtteranceSurface | UtteranceSurfaceResult | None = None,
    memory_anchor_ref: str | None = None,
    cooperation_anchor_ref: str | None = None,
) -> GroundedSemanticResult:
    dictum_bundle, dictum_lineage = _extract_dictum_input(dictum_result_or_bundle)
    surface = _extract_optional_surface(utterance_surface)
    if memory_anchor_ref is not None and not isinstance(memory_anchor_ref, str):
        raise TypeError("memory_anchor_ref must be str when provided")
    if cooperation_anchor_ref is not None and not isinstance(cooperation_anchor_ref, str):
        raise TypeError("cooperation_anchor_ref must be str when provided")

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

    substrate_units: list[GroundedSubstrateUnit] = []
    phrase_scaffolds: list[PhraseScaffold] = []
    operator_carriers: list[OperatorCarrier] = []
    dictum_carriers: list[DictumCarrier] = []
    modus_carriers: list[ModusCarrier] = []
    source_anchors: list[SourceAnchor] = []
    uncertainty_markers: list[UncertaintyMarker] = []
    ambiguity_reasons: list[str] = []
    low_coverage_reasons: list[str] = []
    clause_ranges_by_id: dict[str, list[tuple[int, int]]] = defaultdict(list)

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

    anchor_index, carrier_index, uncertainty_index = _register_surface_cues(
        surface=surface,
        linked_dictum_ids=tuple(candidate.dictum_candidate_id for candidate in dictum_bundle.dictum_candidates),
        source_anchors=source_anchors,
        operator_carriers=operator_carriers,
        modus_carriers=modus_carriers,
        uncertainty_markers=uncertainty_markers,
        start_anchor_index=anchor_index,
        start_carrier_index=carrier_index,
        start_uncertainty_index=uncertainty_index,
    )

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

    if dictum_bundle.conflicts:
        ambiguity_reasons.append("dictum_conflicts_present")
    if dictum_bundle.unknowns:
        ambiguity_reasons.append("dictum_unknowns_present")
    if dictum_bundle.ambiguities:
        ambiguity_reasons.extend(amb.reason for amb in dictum_bundle.ambiguities)

    if surface is None:
        low_coverage_reasons.append("surface_not_provided")
    if not source_anchors:
        low_coverage_reasons.append("source_anchors_sparse")
    if not operator_carriers:
        low_coverage_reasons.append("operator_carriers_sparse")
    if memory_anchor_ref is None:
        low_coverage_reasons.append("m03_anchor_not_provided")
    if cooperation_anchor_ref is None:
        low_coverage_reasons.append("o03_anchor_not_provided")

    low_coverage_mode = bool(low_coverage_reasons)
    reversible_span_mapping_present = bool(surface and surface.reversible_span_map_present)

    bundle = GroundedSemanticBundle(
        source_dictum_ref=dictum_bundle.source_lexical_grounding_ref,
        source_syntax_ref=dictum_bundle.source_syntax_ref,
        source_surface_ref=dictum_bundle.source_surface_ref,
        linked_dictum_candidate_ids=tuple(candidate.dictum_candidate_id for candidate in dictum_bundle.dictum_candidates),
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
        no_final_semantic_resolution=True,
        reason="g01 grounded semantic scaffold generated from l04 candidates without semantic closure",
    )
    gate = evaluate_grounded_semantic_downstream_gate(bundle)
    source_lineage = tuple(
        dict.fromkeys(
            (
                dictum_bundle.source_lexical_grounding_ref,
                dictum_bundle.source_syntax_ref,
                *dictum_lineage,
                *((f"m03:{memory_anchor_ref}",) if memory_anchor_ref else ()),
                *((f"o03:{cooperation_anchor_ref}",) if cooperation_anchor_ref else ()),
            )
        )
    )
    telemetry = build_grounded_semantic_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        reversible_span_mapping_present=reversible_span_mapping_present,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="l04 dictum carriers projected into span-grounded scaffold with unresolved operator/source markers",
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


def _register_surface_cues(
    *,
    surface: UtteranceSurface | None,
    linked_dictum_ids: tuple[str, ...],
    source_anchors: list[SourceAnchor],
    operator_carriers: list[OperatorCarrier],
    modus_carriers: list[ModusCarrier],
    uncertainty_markers: list[UncertaintyMarker],
    start_anchor_index: int,
    start_carrier_index: int,
    start_uncertainty_index: int,
) -> tuple[int, int, int]:
    if surface is None:
        return start_anchor_index, start_carrier_index, start_uncertainty_index

    anchor_index = start_anchor_index
    carrier_index = start_carrier_index
    uncertainty_index = start_uncertainty_index
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

    return anchor_index, carrier_index, uncertainty_index


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
    bundle = GroundedSemanticBundle(
        source_dictum_ref=dictum_bundle.source_lexical_grounding_ref,
        source_syntax_ref=dictum_bundle.source_syntax_ref,
        source_surface_ref=dictum_bundle.source_surface_ref,
        linked_dictum_candidate_ids=tuple(candidate.dictum_candidate_id for candidate in dictum_bundle.dictum_candidates),
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
        low_coverage_reasons=("abstain",),
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
